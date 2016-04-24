# Environments Directory

This directory is used to store Machine and Environment specific configurations.

These custom settings files should be used to store machine-specific and environment-specific
settings. 

Theses files shold be excluded from the github repository. 

A sample of each custom file can be included in the git repository but should NOT contain 
sensitive information such as passwords.

The machine/environment name is passed as an environment variable. when the django app is run.
If no variable is defined the variable will default to "local".

The naming convention for settings files in this directory is:

    settings_{environment}.py

Example files are named as follows:

    settings_{environment}_example.py

The settings_local file is loaded at the end of settings.py.

    try:
        from .envs.settings_local import *
    except ImportError:
        pass
