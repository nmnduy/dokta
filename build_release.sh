#!/bin/bash

pip install pyinstaller
pyinstaller --onefile --clean main.py

echo "Binary file is at ./dist/main"
