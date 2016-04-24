#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client._start_envs
FILE: settings_local.py
Created: 4/23/16 10:49 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import os
from ..utils import Server_Ip, Server_Name

# Set a unique key
# This should override the FAKE_KEY for SECRET_KEY defined in settings.py
SECRET_KEY = "tdy4kyy)9%&3fkfp4$(ofskr7^2qm59h83f^zv9dt_feua!0!$"

# Short system name - use it to prefix file names for things such as logging.
SYSNAME = "fhir_cli"

# Are we running using an SSL Certificate. ie. https://.....
## SSL = True
SSL = False

# Machine Domain name:
DOMAIN = "client.bbonfhir.com"

# DEBUG Settings:
DEBUG = True
DEBUG_SETTINGS = DEBUG

# Allowed Hosts setting:
ALLOWED_HOSTS = []

# Get the Server Domain Name. eg. dev.bbonfhir.com
# ie the server name to address this app
if DEBUG:
    ALLOWED_HOSTS = ['*']

else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', DOMAIN ]

    ALLOWED_HOSTS.append(Server_Ip())
    ALLOWED_HOSTS.append(Server_Name())

# Application name
APPLICATION_TITLE = "FHIR test client"

ADMINS = (
    ('Mark Scrimshire', 'mark@ekivemark.com'),
)

MANAGERS = ADMINS

LOCAL_APPS = [
   # Add machine/environment specific apps here
]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Where will STATIC files be stored.
# Remember to run
# manage.py collectstatic
# to deploy static files on Apache

STATIC_ROOT = '/var/www/html/'+DOMAIN+'/'


######
###
### Logging
###
######
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'mysite.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers':['file'],
            'propagate': True,
            'level':'DEBUG',
        },
        'MYAPP': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

LOGGING['handlers']['file']['filename'] = BASE_DIR + "/../log/" + SYSNAME + ".log"

####
#
# Simple print statement to show envs.settings_local has run
#
####
print("COMPLETED:env.settings_local")

