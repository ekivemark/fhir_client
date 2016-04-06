#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: utils.py
Created: 4/6/16 1:10 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import socket

from threading import local
from django.conf import settings

_user = local()

class CurrentUserMiddleware(object):
    ###
    ### Add to MIDDLEWARE_CLASSES after Authentication middleware
    ###
    def process_request(selfself,request):
        _user.value = request.user


def get_current_user():
    return _user.value


def str2bool(inp):
    output = False
    if inp.upper() == "TRUE":
        output = True
    elif inp.upper() == "FALSE":
        output = False

    return output


def str2int(inp):
    output = 0 + int(inp)

    return output


def notNone(value, default):
    """
    Test value. Return Default if None
    http://stackoverflow.com/questions/4978738/
    is-there-a-python-equivalent-of-the-c-sharp-null-coalescing-operator
    """
    if value is None:
        return default
    else:
        return value


def Server_Ip():
    # use socket to get ip address for this server
    return socket.gethostbyname(socket.gethostname())


def Server_Name():
    # use socket to return server name
    return socket.gethostname()

