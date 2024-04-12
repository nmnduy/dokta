#!/bin/bash

python setup.py install
pip install pyinstaller
pyinstaller --onefile --clean main.py

echo "Binary file is at ./dist/main"
