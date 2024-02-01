def print_green(text, newline=True):
    print(f"\033[32m{text}\033[0m", end="\n" if newline else "")

def print_yellow(text, newline=True):
    print(f"\033[33m{text}\033[0m", end="\n" if newline else "", flush=True)

def print_red(text):
    print(f"\033[31m{text}\033[0m")
