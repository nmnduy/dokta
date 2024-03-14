import sys
import re
import readline
from .exceptions import InputResetException
from .print_colors import print_green, print_yellow
from .config import CONFIG, get_model_config
from .convo_db import Db
from .utils import random_hash



PROMPT = "> "
ANSWER = "🤖 "

OPTION_PASTE = "paste"
OPTIONS = {
    OPTION_PASTE: False,
}
MODELS = [mod["name"] for mod in CONFIG["models"]]
COMMANDS = ["\\model",
            "\\session",
            "\\list_session",
            "\\rename_session",
            "\\messages",
            "\\last_session",
            "\\set <key> <value>",
            "\\help",
            "<endofinput>",
            ]
END_OF_INPUT = re.compile(r"<endofinput>")
MODEL_REGEX = re.compile(r"\\model")
SESSION_REGEX = re.compile(r"\\session")
RENAME_SESSION_REGEX = re.compile(r"\\rename_session")
LIST_SESSION_REGEX = re.compile(r"\\list_session")
MESSAGES_REGEX = re.compile(r"\\messages")
LAST_SESSION_REGEX = re.compile(r"\\last_session")
RANDOM_HASH_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")
SET_OPTION_REGEX = re.compile(r"\\set (\w+) (\w+)")
HELP_REGEX = re.compile(r"\\help")


def print_help():
    print()
    print_yellow("Type your message, then 'Enter' to send.")
    print_yellow("Ctrl + C to exit")
    print()
    print_yellow('You can start multiline input with \'\'\' or """')
    print_yellow('e.g. """Hello!<new line>How are you?""" or \'\'\'Hello!<new line>How are you?\'\'\'')
    print()


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


def get_completer():
    # leave out chat sessions from autocomplete
    # + [
        # item.name for item in Db().get_all_chat_sessions()
        # if not re.match(RANDOM_HASH_REGEX, item.name)
    # ]
    options = MODELS + COMMANDS + list(OPTIONS.keys())
    completer = AutoComplete(list(set(options)))
    return completer



def get_prompt(state, # : State
               ):

    user_message = ""

    # readline.set_completer_delims(' \t\n;')
    readline.set_completer(get_completer().complete)
    readline.parse_and_bind('tab: complete')

    is_multi_line = False
    while True:

        try:

            line = input(PROMPT)
            line = line.replace('\t', '  ')

            if re.match(HELP_REGEX, line):
                print_help()
                user_message = ""
                raise InputResetException()

            if re.match(MODEL_REGEX, line):
                model_match = re.match(r"\\model (.*)", line)
                if model_match:
                    model = model_match.group(1).strip()

                    try:
                        state.max_tokens = get_model_config(model)["max_tokens"]
                    except LookupError:
                        print_yellow("Please enter a valid model.")
                    else:
                        state.model = model
                        print_green(f"Using model: {state.model}. Max context: {state.max_tokens}")
                else:
                    print_yellow("Please enter a model. Like \\model gpt-4")
                user_message = ""
                raise InputResetException()

            if re.match(SET_OPTION_REGEX, line):
                match = re.match(SET_OPTION_REGEX, line)
                if not match:
                    print_yellow("Please enter a valid option. Like \\set <key> <value>")
                    user_message = ""
                    raise InputResetException()
                key, value = match.group(1), match.group(2)
                if key in OPTIONS:
                    value_type = type(OPTIONS[key])
                    value = value_type(value)
                    OPTIONS[key] = value
                    print_green(f"Set option '{key}' to {value}")
                    handle_new_options(key)
                else:
                    print_yellow(f"Option {key} not found.")
                user_message = ""
                raise InputResetException()

            if re.match(SESSION_REGEX, line):
                try:
                    session_name = re.match(r"\\session (.*)", line).group(1).strip()
                except AttributeError:
                    session_name = random_hash()
                db = Db()
                session = db.find_session(session_name)
                if not session:
                    print_green(f"New session: {session_name}")
                    state.session_id = db.create_chat_session(session_name)
                else:
                    print_green(f"Switching to session: {session_name}")
                    state.session_id = session.id
                user_message = ""
                is_multi_line = False
                raise InputResetException()


            if re.match(RENAME_SESSION_REGEX, line):

                # avoid name collision by turnin off autocomplete
                readline.set_completer()

                try:
                    session_name = re.match(r"\\rename_session (.*)", line).group(1).strip()
                except AttributeError:
                    print_yellow("Please enter a session name. Like \\rename_session my_session")

                    readline.set_completer(completer.complete)
                    user_message = ""
                    raise InputResetException()

                db = Db()
                sesh = db.find_session(session_name)
                if sesh:
                    id_ = random_hash()
                    print_yellow(f"Session {session_name} already exists. Replacing it with random id {id_}")
                    db.rename_chat_session(sesh.id, id_)

                db.rename_chat_session(state.session_id, session_name)
                print_green(f"Renamed current session to: {session_name}")
                readline.set_completer(completer.complete)
                user_message = ""
                raise InputResetException()


            if re.match(MESSAGES_REGEX, line):
                db = Db()
                messages = db.get_entries_past_week(state.session_id)
                sorted(messages,
                       key=lambda x: x.created_at,
                       reverse=True)
                print_yellow(f"Messages for session: {state.session_id}")
                print()
                for msg in messages:
                    if msg.role == "user":
                        print(PROMPT + msg.content)
                    if msg.role == "assistant":
                        print(ANSWER + msg.content)
                    print()
                print_yellow("End of messages.")
                print()
                user_message = ""
                raise InputResetException()

            if re.match(END_OF_INPUT, line):
                raise EOFError()

            if re.match(LIST_SESSION_REGEX, line):
                db = Db()
                sessions = db.get_all_chat_sessions()
                print()
                print_yellow("Sessions:")
                for session in sessions:
                    print_yellow(f"  {session.name}")
                user_message = ""
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
                user_message = ""
                raise InputResetException()

            if line.startswith('"""') or line.endswith('"""') or line.startswith("'''") or line.endswith("'''"):

                quote_used = '"""' if line.startswith('"""') or line.endswith('"""') else "'''"

                # Terminate multi-line input
                if is_multi_line and quote_used == quote_type:
                    user_message += line + "\n"
                    break
                # Continue multi-line input because quote is not closed
                elif is_multi_line and quote_used != quote_type:
                    user_message += line + "\n"
                    continue
                # Start multi-line input
                else:
                    is_multi_line = True
                    quote_type = '"""' if line.startswith('"""') or line.endswith('"""') else "'''"
                    user_message += line + "\n"
                    continue

            if not line:  # Check if line is empty
                user_message += "\n"
                continue

            # terminate single line input on ENTER
            if not is_multi_line:
                user_message += line + "\n"
                break

            user_message += line + "\n"

        # trick to reset the prompt after we switch model
        except InputResetException:
            print()
            continue
        except (KeyboardInterrupt, EOFError):
            print("Goodbye! Have a nice day.")
            sys.exit()

        if not user_message.strip():
            print_yellow("Message is empty. Please enter a message.")
            continue

    return user_message


def handle_new_options(key: str):
    if key == OPTION_PASTE:
        if OPTIONS[OPTION_PASTE]:
            readline.set_completer(None)
        else:
            readline.set_completer(get_completer().complete)
