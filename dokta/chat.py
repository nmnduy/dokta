import argparse
import os
import json

import requests
from .structs import State
from .prompt import get_prompt, ANSWER
from .config import get_model_config
from .print_colors import print_yellow, print_red
from .convo_db import setup_database_connection, add_entry, get_entries_past_week, DB_NAME, Db
from .constants import ROLE_USER, ROLE_ASSISTANT



# 'cl100k_base' is for gpt-4 and gpt-3.5-turbo
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
#ENCODER = tiktoken.get_encoding('cl100k_base')
STATE = State(model='', max_tokens=0)
ANTHROPIC_MODEL_MAP = {
    "opus": "claude-3-opus-20240229",
    "sonnet": "claude-3-sonnet-20240229",
    "haiku": "claude-3-haiku-20240307",
}

BACKEND_OPENAI = "openai"
BACKEND_OLLAMA = "ollama"
BACKEND_ANTHROPIC = "anthropic"
BACKEND_GROQ = "groq"


def messages_to_prompt(messages): # -> str:
    prompt = ""
    for message in messages:
        prompt += f"{message['role']}: {message['content']}\n"
    return prompt


def load_conversation_history(db_session, state: State): # -> List[Dict[str, str]]:
    max_tokens = state.max_tokens
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



def chat(messages, state: State):
    config = get_model_config(state.model)
    backend = config.get("backend", BACKEND_OPENAI)
    if backend == BACKEND_OLLAMA:
        return chat_with_ollama(messages, state)
    elif backend == BACKEND_ANTHROPIC:
        return chat_with_anthropic(messages, state)
    elif backend == BACKEND_GROQ:
        return chat_with_grog(messages, state)
    else:
        return chat_with_openai(messages, state)


import time
from functools import wraps

def retry(max_attempts=3, delay_ms=1000):
    """
    A decorator that retries a function up to `max_attempts` times if it raises an exception.

    Args:
        max_attempts (int): The maximum number of attempts to make.
        delay_ms (int): The delay_ms in milliseconds between each attempt.

    Returns:
        A decorator that retries the decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Function {func.__name__} raised an exception: {e}")
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"Retrying function {func.__name__} ({attempts}/{max_attempts})")
                        time.sleep(delay_ms / 1000)  # Convert delay_ms from milliseconds to seconds
            raise Exception(f"Function {func.__name__} failed after {max_attempts} attempts.")
        return wrapper
    return decorator

@retry(max_attempts=3, delay_ms=500)
def chat_with_anthropic(messages,  # List[Dict[str, str]]
                        state: State):
    conversation = [msg for msg in messages.copy() if msg['content'].strip() != '']

    i = 0
    while i < len(conversation) - 1:
        if conversation[i]['role'] == conversation[i+1]['role']:
            conversation[i]['content'] += '\n' + conversation[i+1]['content']
            del conversation[i+1]
        else:
            i += 1

    actual_model = ANTHROPIC_MODEL_MAP[state.model]
    if not actual_model:
        raise ValueError(f"Model {state.model} not found in ANTHROPIC_MODEL_MAP")

    # context is 100k-200k tokens
    # but output is capped at 4096 tokens
    max_tokens = 4096

    if "ANTHROPIC_API_KEY" not in os.environ:
        print_red("Please set env var ANTHROPIC_API_KEY")
        exit(1)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": actual_model,
            "max_tokens": max_tokens,
            "messages": conversation,
            "stream": True
        }
    )
    for line in response.iter_lines():
        line = line.decode('utf-8')
        # if line is a JSON with 'error', treat this as an error
        try:
            chunk = json.loads(line)
            if 'error' in chunk:
                raise Exception("Error receiving response from anthropic server: " + str(chunk['error']))
        except json.decoder.JSONDecodeError:
            pass
        if line.startswith('data: '):
            chunk = json.loads(line[6:].strip())
            if chunk['type'] == 'content_block_delta':
                yield chunk['delta']['text']
            elif chunk['type'] == 'error':
                raise Exception("Error receiving response from anthropic server: " + str(chunk['error']))


@retry(max_attempts=3, delay_ms=500)
def chat_with_grog(messages, # List[Dict[str, str]]
                   state: State):

    max_tokens = state.max_tokens

    if "GROQ_API_KEY" not in os.environ:
        print_red("Please set env var GROQ_API_KEY")
        exit(1)

    url = "https://api.groq.com/openai/v1/chat/completions"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": state.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True
        })
    for line in response.iter_lines():
        # payload we want look like this b'data: {"id":"chatcmpl-e38cab93-3a9d-971e-acec-700dacf6a4c8","object":"chat.completion.chunk","created":1711526569,"model":"mixtral-8x7b-32768","system_fingerprint":"fp_1cc6d039b0","choices":[{"index":0,"delta":{"content":" scope"},"logprobs":null,"finish_reason":null}]}'
        if line.startswith(b'data: '):
            try:
                chunk = json.loads(line[6:].strip())
                if chunk['object'] == 'chat.completion.chunk':
                    yield chunk['choices'][0]['delta']['content']
                elif chunk['object'] == 'error':
                    raise Exception("Error receiving response from groq server: " + chunk['error'])
            except (KeyError, json.decoder.JSONDecodeError):
                pass



def chat_with_ollama(messages, # List[Dict[str, str]]
                     state: State):
    response = requests.post(
        'http://localhost:11434/api/chat',
        json={
            "model": state.model,
            "messages": messages,
        },
        stream=True
    )
    for line in response.iter_lines():
        if line:
            # line looks like this:
            # {'model': 'openhermes2.5-mistral:7b', 'created_at': '2024-04-18T15:11:00.372464Z', 'message': {'role': 'assistant', 'content': 'Hello'}, 'done': False}
            chunk = json.loads(line.decode('utf-8'))
            if 'error' in chunk:
                raise Exception("Error receiving response from ollama server: " + chunk['error'])
            yield chunk['message']['content']
            if chunk['done']:
                break



@retry(max_attempts=3, delay_ms=500)
def chat_with_openai(messages, # List[Dict[str, str]]
                     state: State):
    if "OPENAI_API_KEY" not in os.environ:
        print_red("Please set env var OPENAI_API_KEY")
        exit(1)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(os.environ["OPENAI_API_KEY"]),
    }
    
    data = {
        "model": state.model,
        "messages": messages,
        "max_tokens": state.max_tokens,
        "n": 1,
        "temperature": 0.7,
        "stream": True,
    }

    timeout = 40
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)

        if response.status_code != 200:
            print(f"Error: {response.text}")
            return None

        response.raise_for_status()

        for chunk in response.iter_lines():
            line = chunk.decode('utf-8')
            if line.startswith('data: '):
                try:
                    try:
                        json_chunk = json.loads(line[6:].strip())
                    except json.JSONDecodeError:
                        # not a valid JSON, skip
                        continue
                    chunk_content = json_chunk['choices'][0]['delta']['content']
                    if chunk_content:
                        yield chunk_content
                except KeyError as error:
                    if str(error) == 'content':
                        pass
                except Exception as error:
                    print("Failed to process chunk", chunk)
    
    except requests.exceptions.RequestException as e:

        import pdb; pdb.set_trace()
        print(f"Error: {e}")
        return None


def count_tokens(text):
    return len(text) // 4


def main():
    model = os.environ.get("CHATGPT_CLI_MODEL", "gpt-3.5-turbo")
    max_tokens = get_model_config(model)["max_tokens"]

    first_use = False
    if not Db().get_last_session():
        first_use = True

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

        db_session = setup_database_connection(DB_NAME)
        add_entry(db_session, ROLE_USER, question.strip(), STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow(ANSWER, newline=False)
        for chunk in chat(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        add_entry(db_session,
                  ROLE_ASSISTANT,
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

        db_session = setup_database_connection(DB_NAME)
        add_entry(db_session, ROLE_USER, args.question, STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow(ANSWER, newline=False)
        for chunk in chat(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        add_entry(db_session,
                  ROLE_ASSISTANT,
                  ai_response,
                  STATE.session_id,
                  )

        print('\a')
        exit(0)

    print_yellow(f"Using model: {model}. Context length: {max_tokens}")
    if first_use:
        print_yellow(f"\\help for help. \\model to change model. \\session to go to a previous session. \\rename_session to rename this session. Ctrl + c quit.")

    db_session = setup_database_connection(DB_NAME)

    while True:
        user_message = get_prompt(STATE).strip()

        # if count_tokens(user_message) > max_tokens:
        #     print("Your message is too long. Please try again.")
        #     continue

        add_entry(db_session, ROLE_USER, user_message, STATE.session_id)

        conversation_history = load_conversation_history(db_session, STATE)
        if not conversation_history:
            raise ValueError("Conversation history is empty")

        ai_response = ""
        print()
        print_yellow(ANSWER)
        for chunk in chat(conversation_history, STATE):
            print(chunk, end="")
            ai_response += chunk

        print('\a')

        # remove the "assistant:" prefix for ollam
        if ai_response.startswith("assistant:"):
            ai_response = ai_response[10:].strip()

        add_entry(db_session,
                  ROLE_ASSISTANT,
                  ai_response,
                  STATE.session_id,
                  model=STATE.model,
                  )
        print()



if __name__ == "__main__":
    main()
