#!/usr/bin/python

#SWAT imports with hack for working around Aros requiring oauth2client v1.4.7
import virtualenv
import pip
import os
# create and activate the virtual environment
venv_dir = os.path.join(os.path.expanduser("."), ".venv")
virtualenv.create_environment(venv_dir, site_packages=True)
execfile(os.path.join(venv_dir, "bin", "activate_this.py"))