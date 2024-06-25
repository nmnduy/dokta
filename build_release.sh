#!/bin/bash

if ! command -v pip &> /dev/null
then
    echo "pip could not be found, please install pip first."
    exit 1
fi

pip install -r requirements.txt

pip install pyinstaller

pyinstaller --onefile --clean main.py

echo "Binary file is at ./dist/main"
