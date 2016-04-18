#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: state
Created: 4/15/16 10:05 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from uuid import uuid4

from django.conf import settings
from django.utils.timezone import now

from ..models import Session_State

AUTH_URL= settings.OAUTH_TEST_INFO['AUTH_URL']
CLIENT_ID = settings.OAUTH_TEST_INFO['CLIENT_ID']


def create_state():

    state_save = {'state': uuid4().urn[9:],'AUTH_URL': AUTH_URL,'CLIENT': CLIENT_ID}
    if settings.DEBUG:
        print("State to save:", state_save)
    saved = save_created_state(state_save)
    if settings.DEBUG:
        print("Saved:", saved)
        print("Returned State:", state_save)

    return state_save['state']


def get_state(client, auth):
    """
    Get state from Session_State
    :return:
    """

    try:
        ss = Session_State.objects.get(auth=auth, name=client)
        return ss.state

    except Session_State.DoesNotExist:
        return None


def save_created_state(state):

    print("Saving Created State:", state)

    try:
        session_state = Session_State.objects.get(auth=state['AUTH_URL'],
                                                  name=state['CLIENT'])
        session_state.state = state['state']
        session_state.save()
    except Session_State.DoesNotExist:
        session_state = Session_State.objects.create(auth=state['AUTH_URL'],
                                                     name=state['CLIENT'],
                                                     state=state['state'])

    if settings.DEBUG:
        print("Session_state:", session_state)

    return state['state']


def is_valid_state(state):

    try:
        session_state = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print('Check state:', session_state, " Found")
        return True
    except Session_State.DoesNotExist:
        if settings.DEBUG:
            print('Check state:', state, " Does Not Exist")
        return False


def save_code(state, code):
    """Write Code to State record in Session_State"""

    try:
        session_state = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print('Checked state:', session_state)
        session_state.code = code
        session_state.save()
        if settings.DEBUG:
            print("Saved Code:", code )
        return code

    except Session_State.DoesNotExist:
        return None


def get_code(client, auth):
    """
    Get code from Session_State
    :return:
    """

    try:
        ss = Session_State.objects.get(auth=auth, name=client)
        return ss.code

    except Session_State.DoesNotExist:
        return None


def save_tokens(state, access, refresh, expires=36000):
    """

    :param code:
    :param access:
    :param refresh:
    :param expires=36000
    :return:
    """

    try:
        ss = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print('found by state:', ss)
        ss.atoken = access
        ss.rtoken = refresh
        ss.expires = now() + expires
        ss.save()
        if settings.DEBUG:
            print("Saved State/Access/Refresh:", state, access, refresh)
        return access

    except Session_State.DoesNotExist:
        return None


def get_access(state):
    """

    :param client:
    :param auth:
    :return:
    """

    try:
        ss = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print('Access found by State:', ss.atoken)

        return ss.atoken

    except Session_State.DoesNotExist:
        return None


def get_refresh(state):
    """

    :param client:
    :param auth:
    :return:
    """

    try:
        ss = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print('Refresh_token found by State:', ss.rtoken)

        return ss.rtoken

    except Session_State.DoesNotExist:
        return None


def access_expired(state):
    """Check for expired access token"""

    try:
        ss = Session_State.objects.get(state=state)
        if settings.DEBUG:
            print("Is expired:", ss.is_expired, "(", ss.expires, " < ", now())
        if ss.is_expired:
            return True
        else:
            return False
    except Session_State.DoesNotExist:
        return True


def get_tokens(state):
    """ Get access, refresh and expires
        return in dict
    """

    tokens = {}

    try:
        ss = Session_State.objects.get(state=state)
        tokens['access_token'] = ss.atoken
        tokens['refresh_token'] = ss.rtoken
        tokens['expires'] = ss.expires
        tokens['expired'] = ss.is_expired
        return tokens
    except Session_State.DoesNotExist:
        return None
