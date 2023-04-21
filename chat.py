import os
import sys
import readline
import json
import openai
from transformers import GPT2Tokenizer
from convo_db import setup_database_connection, add_entry, get_entries_past_week


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
    max_tokens = int(os.environ["MAX_TOKENS"])
    print_green(f"Using model: {model}. Max tokens: {max_tokens}")
    print()
    print(f"\033[33mCtrl + D to submit a message\033[0m")
    print(f"\033[33mCtrl + C to exit. Or type quit\033[0m")
    print()
    db_session = setup_database_connection("convo_db.sqlite")()

    while True:
        print()
        print(f"\033[32mYou:\033[0m")
        try:
            user_message = ""
            while True:
                line = input()
                user_message += line + "\n"
        # ctrl + z or ctrl + d to submit
        except EOFError:
            pass
        except KeyboardInterrupt:
            print("Goodbye! Have a nice day.")
            sys.exit()

        if not user_message.strip():
            print_yellow("Message is empty. Please enter a message.")
            continue

        if user_message.lower() in ["quit", "exit", "bye"]:
            break

        if user_message.startswith("\model"):
            model = user_message.split()[1]
            print("Switching to model:", model)
            continue

        if user_message.startswith("\max_tokens"):
            max_tokens = int(user_message.split()[1])
            print("Setting model token limit to:", max_tokens)
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
