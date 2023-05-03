import re
import os
import sys
import readline
import json
import openai
from transformers import GPT2Tokenizer
from convo_db import setup_database_connection, add_entry, get_entries_past_week


CONFIG = json.load(open("config.json"))


class ModelSwitch(Exception):
    pass


def parse_model_change(line: str):
    model = line.split(" ")[1]
    try:
        model_config = next(m for m in CONFIG["models"] if m['name'] == model)
    except StopIteration:
        raise LookupError(f"Model {model} not found in config.json")
    max_tokens = model_config["max_tokens"]
    return model, max_tokens


def print_green(text):
    print(f"\033[32m{text}\033[0m")

def print_yellow(text):
    print(f"\033[33m{text}\033[0m")



def load_conversation_history(session, max_tokens=2048): # -> List[Dict[str, str]]:
    entries = get_entries_past_week(session)

    token_count = 0
    conversation_text = []
    for entry in reversed(entries):
        entry_text = f"{entry.role}: {entry.content}\n"
        entry_token_count = count_tokens(entry_text)
        if token_count + entry_token_count <= max_tokens:
            conversation_text.append({"role": entry.role, "content": entry.content})
            token_count += entry_token_count
        else:
            break
    return conversation_text[::-1]


def chat_with_openai(prompt, model):
    response = openai.ChatCompletion.create(
        model=model,
        messages=prompt,
        # max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].message['content']


def count_tokens(text):
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    tokens = tokenizer.encode(text)
    return len(tokens)


def main():
    model = os.environ["CHATGPT_CLI_MODEL"]
    try:
        model_config = next(m for m in CONFIG["models"] if m['name'] == model)
    except StopIteration:
        raise LookupError(f"Model {model} not found in config.json")
    max_tokens = model_config["max_tokens"]

    print_green(f"Using model: {model}. Max tokens: {max_tokens}")
    print()
    print(f"\033[33mCtrl + D on an empty line to submit a message\033[0m")
    print(f"\033[33mCtrl + C to exit\033[0m")
    print()
    db_session = setup_database_connection("convo_db.sqlite")()

    model_regex = re.compile(r"\\model\s(\w+)")

    while True:
        print()
        print(f"\033[32mYou:\033[0m")
        try:
            user_message = ""
            while True:
                line = input()

                if not line:  # Check if line is empty
                    user_message += "\n"

                if re.match(model_regex, line):
                    model, max_tokens = parse_model_change(line)
                    print_green(f"Using model: {model}. Max tokens: {max_tokens}")
                    raise ModelSwitch()

                user_message += line + "\n"

        # ctrl + z or ctrl + d to submit
        except EOFError:
            pass
        # trick to reset the prompt after we switch model
        except ModelSwitch:
            continue
        except KeyboardInterrupt:
            print("Goodbye! Have a nice day.")
            sys.exit()

        if not user_message.strip():
            print_yellow("Message is empty. Please enter a message.")
            continue

        print()
        print(f"\033[33mOne moment...\033[0m")

        if count_tokens(user_message) > max_tokens:
            print("Your message is too long. Please try again.")
            continue

        add_entry(db_session, "user", user_message)

        conversation_history = load_conversation_history(db_session, max_tokens=max_tokens)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = chat_with_openai(conversation_history, model)
        add_entry(db_session, "assistant", ai_response)

        print()
        print(f"\033[33mAssistant: \033[0m{ai_response}")
        print()


if __name__ == "__main__":
    main()
