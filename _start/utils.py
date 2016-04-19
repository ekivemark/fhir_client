#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: utils.py
Created: 4/6/16 1:10 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import datetime
import json
import socket

from django.conf import settings
from django.http import QueryDict
from django.utils.timezone import now


from threading import local

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


def update_dict(context, context_override={}):
    """Add dict to existing dict with overwrites"""

    for key, value in context_override.items():
        context[key] = value

    return context


def look_at_request(request, all=False):
    """Analyze headers and GET"""

    print("===================-----------------=================")
    print("Request:", request)

    if request.method == 'GET':
        print("GET in", request)
    elif request.method == 'POST':
        print("POST in", request.method)
        if not QueryDict(request.body) == QueryDict(None):
            data = QueryDict(request.body)
            print("POST Body:", data)
    else:
        print("not a GET or Post in:", request.method )

    if len(request.META) > 0:
        other_values = []
        for key, value in request.META.items():
            if "HTTP_" in key or "CONTENT" in key or "X-FRAME" in key.upper():
                print("Header:", key, ":", request.META[key])
            else:
                other_values.append(key)

        print("Other Values:", other_values)

    else:
        print(request.META)

    print("===================-----------------=================")

    return


def now_add_secs(secs):
    if settings.DEBUG:
        print("Now:", now())
    fulldate = datetime.datetime.now()
    fulldate += datetime.timedelta(seconds=secs)
    if settings.DEBUG:
        print("Then:", fulldate)
    return fulldate

