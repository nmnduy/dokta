import sys
import re
import json
import readline
from .exceptions import ModelSwitch
from .print_colors import print_green, print_yellow
from .config import CONFIG, get_model_config



MODELS = [mod["name"] for mod in CONFIG["models"]]
MODEL_REGEX = re.compile(r"\\model")






def model_complete(text, state):
    volcab = MODELS
    results = [x for x in volcab if x.startswith(text)] + [None]
    # print()
    # print("TEXT: ", text)
    # print("RESULTS: ", results)
    if text == results[state]:
        return None
    return results[state]



def switch_model(): #  -> str
    print_yellow(f"Options: {MODELS}")

    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(' \t\n')

    readline.set_completer(model_complete)

    line = input("Model: ")

    model = line.strip()
    return model



def get_prompt(state, # : State
               ):

    user_message = ""
    while True:
        try:
            line = input()

            if not line:  # Check if line is empty
                user_message += "\n"

            if re.match(MODEL_REGEX, line):
                model = switch_model()
                state.model = model
                state.max_tokens = get_model_config(model)["max_tokens"]
                print_green(f"Using model: {state.model}. Max context: {state.max_tokens}")
                print_green("You: ")
                user_message = ""
                raise ModelSwitch()

            user_message += line + "\n"

        # ctrl + z or ctrl + d to submit
        except EOFError:
            break
        # trick to reset the prompt after we switch model
        except ModelSwitch:
            continue
        except KeyboardInterrupt:
            print("Goodbye! Have a nice day.")
            sys.exit()

        if not user_message.strip():
            print_yellow("Message is empty. Please enter a message.")
            continue

    return user_message
