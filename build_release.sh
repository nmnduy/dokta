#!/bin/bash

pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --clean main.py

echo "Binary file is at ./dist/main"
