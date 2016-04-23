#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: auth
Created: 4/8/16 3:57 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.conf import settings
from requests.auth import HTTPBasicAuth

def set_Basic_Auth_Header(key, value):
    """
    Set Basic Auth. Typically key is username,value is password
    format:
    headers = { 'Authorization' : 'Basic %s' %  userAndPass }
    c.request('GET', '/', headers=headers)
    """

    auth = HTTPBasicAuth(key, value)

    if settings.DEBUG:
        print("Auth:", auth)

    return auth
