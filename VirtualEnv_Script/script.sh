#!/usr/bin/env bash

#Before running this, we need to 'chmod +x script.sh' to grant write permissions to the script and then run './script.sh'

python virtualenv_creator.py
source "./.venv/bin/activate"
# Virtualenv created now!
python version6.py