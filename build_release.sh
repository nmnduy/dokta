#!/bin/bash

pip install pyinstaller
pyinstaller --onefile --clean --name dokta dokta/chat.py
