import re
import argparse
import os
import sys
import json
import time
import openai
import tiktoken
from retrying import retry
from .structs import State
from .prompt import get_prompt
from .config import get_model_config
from .print_colors import print_green, print_yellow
from .convo_db import setup_database_connection, add_entry, get_entries_past_week, DB_NAME, Db



# 'cl100k_base' is for gpt-4 and gpt-3.5-turbo
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
#ENCODER = tiktoken.get_encoding('cl100k_base')
STATE = State(model='', max_tokens=0)




def load_conversation_history(db_session, state: State): # -> List[Dict[str, str]]:
    max_tokens = state.max_tokens
    model = state.model
    session_id = state.session_id
    entries = get_entries_past_week(db_session, session_id=session_id)

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





@retry(stop_max_attempt_number=3, wait_fixed=2000)
def chat_with_openai(prompt, state: State):
    model = state.model
    response = openai.ChatCompletion.create(
        model=model,
        messages=prompt,
        # max_tokens=150,
        n=1,
        stop=None,
        temperature=1.0,
        timeout=120,
        stream=True,
    )
    for chunk in response:
        try:
            yield chunk.choices[0].delta['content']
        except KeyError as error:
            if str(error) == 'content':
                pass
        except:
            print("Failed to process chunk", chunk)


def count_tokens(text):
    return len(text) // 4


def main():
    model = os.environ["CHATGPT_CLI_MODEL"]
    max_tokens = get_model_config(model)["max_tokens"]
    STATE = State(model, max_tokens, session_id=Db().create_chat_session())

    parser = argparse.ArgumentParser(description='Chat with GPT-3')
    parser.add_argument('--question', '-q', type=str, help='Question for the assistant')
    parser.add_argument('--file', '-f', type=str, help='File containing questions for the assistant')

    args = parser.parse_args()

    # file mode
    if args.file:
        with open(args.file, 'r') as file:
            question = file.read()

        if count_tokens(question) > max_tokens:
            print("Your message is too long. Please try again.")
            return

        db_session = setup_database_connection(DB_NAME)()
        add_entry(db_session, "user", question.strip(), STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow("Assistant:" + "\n")
        for chunk in chat_with_openai(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        add_entry(db_session,
                  "assistant",
                  ai_response,
                  STATE.session_id,
                  )

        print('\a')
        exit(0)

    # one-off mode
    elif args.question:
        if count_tokens(args.question) > max_tokens:
            print("Your message is too long. Please try again.")
            exit(1)

        db_session = setup_database_connection(DB_NAME)()
        add_entry(db_session, "user", args.question, STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow("Assistant:" + "\n")
        for chunk in chat_with_openai(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        add_entry(db_session,
                  "assistant",
                  ai_response,
                  STATE.session_id,
                  )

        print('\a')
        exit(0)

    # conversation mode
    print()
    print_yellow("Type your message, then 'Enter' to send.")
    print_yellow("Ctrl + C to exit")
    print_yellow('If you want multi-line input, wrap your message in triple quotes. e.g. """Hello!"""')
    print()
    print_green(f"Using model: {model}. Context length: {max_tokens}")
    db_session = setup_database_connection(DB_NAME)()

    while True:
        user_message = get_prompt(STATE).strip()

        if count_tokens(user_message) > max_tokens:
            print("Your message is too long. Please try again.")
            continue

        add_entry(db_session, "user", user_message, STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow("Assistant:" + "\n")
        for chunk in chat_with_openai(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        print('\a')

        add_entry(db_session,
                  "assistant",
                  ai_response,
                  STATE.session_id,
                  model=STATE.model,
                  )



if __name__ == "__main__":
    main()
