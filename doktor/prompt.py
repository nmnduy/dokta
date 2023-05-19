import sys
import re
import json
import readline
from .exceptions import InputResetException
from .print_colors import print_green, print_yellow
from .config import CONFIG, get_model_config
from .convo_db import Db



MODELS = [mod["name"] for mod in CONFIG["models"]]
COMMANDS = ["\\model",
            "\\session",
            "\\list_session",
            "\\rename_session",
            "\\messages",
            "\\last_session",
            ]
MODEL_REGEX = re.compile(r"\\model")
SESSION_REGEX = re.compile(r"\\session")
RENAME_SESSION_REGEX = re.compile(r"\\rename_session")
LIST_SESSION_REGEX = re.compile(r"\\list_session")
MESSAGES_REGEX = re.compile(r"\\messages")
LAST_SESSION_REGEX = re.compile(r"\\last_session")
RANDOM_HASH_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")



def model_complete(text, state):
    results = [x for x in MODELS if x.startswith(text)] + [None]
    if text == results[state]:
        return None
    return results[state]





class AutoComplete(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if not text:
                self.matches = self.options[:]
            else:
                self.matches = [s for s in self.options
                                if s and s.startswith(text)]

        try:
            return self.matches[state]
        except IndexError:
            return None



def command_complete(text, state):
    results = [x for x in options if x.startswith(text)] + [None]
    return results[state]




def get_prompt(state, # : State
               ):

    user_message = ""

    options = MODELS + COMMANDS + [
        item.name for item in Db().get_all_chat_sessions()
        if not re.match(RANDOM_HASH_REGEX, item.name)
    ]
    completer = AutoComplete(list(set(options)))
    readline.set_completer_delims(' \t\n;')
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    print()
    print(f"\033[32mYou:\033[0m")

    while True:

        try:

            line = input()

            if not line:  # Check if line is empty
                user_message += "\n"


            if re.match(MODEL_REGEX, line):

                model = re.match(r"\\model (.*)", line).group(1)

                try:
                    state.max_tokens = get_model_config(model)["max_tokens"]
                except LookupError:
                    print_yellow("Please enter a valid model.")
                    raise InputResetException()

                state.model = model
                print_green(f"Using model: {state.model}. Max context: {state.max_tokens}")
                user_message = ""
                raise InputResetException()


            if re.match(SESSION_REGEX, line):
                try:
                    session_name = re.match(r"\\session (.*)", line).group(1)
                except AttributeError:
                    print_yellow("Please enter a session name. Like \\session my_session")
                else:
                    db = Db()
                    session = db.find_session(session_name)
                    if not session:
                        print_green(f"New session: {session_name}")
                        state.session_id = db.create_chat_session(session_name)
                    else:
                        print_green(f"Switching to session: {session_name}")
                        state.session_id = session.id
                raise InputResetException()


            if re.match(RENAME_SESSION_REGEX, line):

                # avoid name collision by turnin off autocomplete
                readline.set_completer()

                try:
                    session_name = re.match(r"\\rename_session (.*)", line).group(1)
                except AttributeError:
                    print_yellow("Please enter a session name. Like \\rename_session my_session")

                if Db().find_session(session_name):
                    print_yellow(f"Session {session_name} already exists.")
                    raise InputResetException()
                else:
                    db = Db()
                    db.rename_chat_session(state.session_id, session_name)
                    print_green(f"Renamed session to: {session_name}")
                    raise InputResetException()


            if re.match(MESSAGES_REGEX, line):
                db = Db()
                messages = db.get_entries_past_week(state.session_id)
                sorted(messages,
                       key=lambda x: x.created_at,
                       reverse=True)
                for msg in messages:
                    if msg.role == "user":
                        print_green(f"You: {msg.content}" + "\n")
                    if msg.role == "assistant":
                        print(f"Assistant: {msg.content}" + "\n")
                raise InputResetException()



            if re.match(LIST_SESSION_REGEX, line):
                db = Db()
                sessions = db.get_all_chat_sessions()
                print()
                print_yellow("Sessions:")
                for session in sessions:
                    print_yellow(f"  {session.name}")
                raise InputResetException()


            if re.match(LAST_SESSION_REGEX, line):
                db = Db()
                try:
                    offset = re.match(r"\\last_session (\d+)", line).group(1)
                except AttributeError:
                    offset = 1
                session = db.get_last_session(offset)
                if not session:
                    print_red("No last session found.")
                else:
                    print_green(f"Switching to session: {session.name}")
                    state.session_id = session.id
                raise InputResetException()

            user_message += line + "\n"

        # ctrl + z or ctrl + d to submit
        except EOFError:
            if not user_message.strip():
                print("Buh bye")
                sys.exit()
            break
        # trick to reset the prompt after we switch model
        except InputResetException:
            print()
            print_green(f"You:")
            continue
        except KeyboardInterrupt:
            print("Goodbye! Have a nice day.")
            sys.exit()

        if not user_message.strip():
            print_yellow("Message is empty. Please enter a message.")
            continue

    return user_message
