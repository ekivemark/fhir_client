#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: access
Created: 4/15/16 8:36 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json
import requests

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import (authenticate,
                                 login,
                                 logout)
from django.contrib import messages
from django.core.urlresolvers import reverse

from django.http import QueryDict
from django.shortcuts import (HttpResponseRedirect,
                              render_to_response,
                              RequestContext)

from django.utils.timezone import now
from _start.utils import look_at_request

from .fhir_connect import FHIRConnect
from .state import create_state, save_code, get_code, get_state, get_tokens, revoke_tokens

FHIR_CLIENT_ID = settings.OAUTH_TEST_INFO['CLIENT_ID']
FHIR_CLIENT_SECRET = settings.OAUTH_TEST_INFO['CLIENT_SECRET']
FHIR_REDIRECT_URI = settings.OAUTH_TEST_INFO['REDIRECT_URI']

def connect(request):
    state = create_state()
    """this function is called when user click to signin to FHIR Service"""
    fhir_service = FHIRConnect(FHIR_CLIENT_ID, FHIR_CLIENT_SECRET)

    params = {'redirect_uri': FHIR_REDIRECT_URI,
              'response_type': 'code',
              'state': state}

    # auth_url = fhir_service.get_authorize_url(redirect_uri=FHIR_REDIRECT_URI)
    auth_url = fhir_service.get_authorize_url(**params)
    # redirect(auth_url)
    return HttpResponseRedirect(auth_url)

def authorize(request):
    """this function is called when user hits FHIR_REDIRECT_URI"""

    if settings.DEBUG:
        print("in the Authorize")
        look_at_request(request, True)
        print('back in Authorize from request analysis')
    if 'code' in request.GET:
        code = request.GET['code']
    else:
        info = request.GET.copy()
        print(info)
        msg = ""
        for k, v in info.items():
            msg += "{%s:%s}" % (k, v)

        messages.error(request,"There was a problem logging in to the remote server."
                               "Did you authorize the access? %s" % msg)
        #aise Exception("Can't get code from url")
        return HttpResponseRedirect(reverse('home'))

    state = request.GET['state']
    coded = save_code(state, code)
    if settings.DEBUG:
        print("==================================================")
        print("Coded with State and Code:", coded, "|", state, "|", code)
        print("==================================================")

    fhir_service = FHIRConnect(FHIR_CLIENT_ID, FHIR_CLIENT_SECRET)
    #session = fhir_service.get_session(code, state, FHIR_REDIRECT_URI)

    session = fhir_service.get_a_session(code, state, FHIR_REDIRECT_URI)
    print("Session in authorize:", session)
    print(session.text)
    info = session.json()
    payload = {'grant_type': 'authorization_code',
               'client_id': FHIR_CLIENT_ID,
               'client_secret': FHIR_CLIENT_SECRET,
               'code': code,
               'state': state,
               'token_type': "Bearer",
               'access_token': info['access_token'],
               }
    headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Authorization': 'Bearer ' + info['access_token']}
    r = requests.get(settings.OAUTH_TEST_INFO['BASE']+"/api/v1/me?_format=json",
                     data=payload, headers=headers)

    print("R got us this info:", r.text)
    #result = r.json()
    result = json.loads(r.text, object_pairs_hook=OrderedDict)

    content = OrderedDict(result)
    # result = session.get(settings.OAUTH_TEST_INFO['BASE']+"/api/v1/me?_format=json")

    # result = fhir_service.oauth_access(code,
    #                                    state,
    #                                    FHIR_REDIRECT_URI,
    #                                    "/api/v1/me?_format=json",
    #                                    method="GET" )

    if settings.DEBUG:
        print("Result from oauth_access:" , result)
    # Get the User Info
    #result = session.get(settings.OAUTH_TEST_INFO['BASE']+"/api/v1/me?_format=json")

    context = {'template': "result.html",
               'display': "User info:",
               'text': content['text'],
               'content': json.dumps(content, indent=4, sort_keys=False)}
    return render_to_response(context['template'],
                              RequestContext(request,
                                             context))


def fhir_patient(request):
    """ Call fhir_enquiry with context
    """

    if settings.DEBUG:
        print("in fhir_patient")
    fhir_service = FHIRConnect(FHIR_CLIENT_ID, FHIR_CLIENT_SECRET)

    context = {}
    context['ask'] = "/api/v1/Patient?_format=json"
    context['display'] = "Patient via fhir_patient"

    if settings.DEBUG:
        print("Got context...", context)


    state = get_state(FHIR_CLIENT_ID, fhir_service.authorize_url)
    code = get_code(FHIR_CLIENT_ID, fhir_service.authorize_url)
    tokens = get_tokens(state)

    if tokens['access_token'] == "" and tokens['refresh_token'] == "":
        if settings.DEBUG:
            print("No tokens - do a login")
        next = settings.DOMAIN+"/fhir_patient"
        return HttpResponseRedirect(reverse("connect"), {'next': next})

    if settings.DEBUG:
        print("==================================================")
        print("Tokens:", tokens, " State:", state, " Code:", code)
        print("==================================================")
    if tokens['expires_in'] <= now() :
        if settings.DEBUG:
            print("Tokens are expired:", tokens)
        tokens = fhir_service.renew_tokens(code, state, tokens)
        if settings.DEBUG:
            print("tokens updated to:", tokens)

    payload = {'grant_type': 'authorization_code',
               'client_id': FHIR_CLIENT_ID,
               'client_secret': FHIR_CLIENT_SECRET,
               'code': code,
               'state': state,
               'token_type': "Bearer",
               'access_token': tokens['access_token'],
               }


    headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Authorization': 'Bearer ' + tokens['access_token']}

    r = requests.get(settings.OAUTH_TEST_INFO['BASE'] + context['ask'],
                     data=payload,
                     headers=headers)

    #result = fhir_enquiry(request, context_override=context)

    convert = json.loads(r.text, object_pairs_hook=OrderedDict)

    content = OrderedDict(convert)
    if 'text' in content:
        context['text'] = content['text']
    context['content'] = json.dumps(content, indent=4)
    #
    # if settings.DEBUG:
    #     print("Session:", session)
    # context['session'] = session
    context['template'] = "result.html"

    return render_to_response(context['template'],
                              RequestContext(request,
                                             context))


def userlogin(request):

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request,"This account is inactive")
            return HttpResponseRedirect(reverse('home'))
    else:
        messages.error(request, "invalid logon")
        return HttpResponseRedirect(reverse('home'))


def userlogout(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect(reverse('home'))


def remote_logout(request):

    r = revoke_tokens()

    if r.status_code == 200:
        messages.info(request,
                      "Remote access tokens have been revoked. Do remote login to reconnect.")
    else:
        messages.error("Problem with remote logout. %s:%2" % (r.status, r.text))

    return HttpResponseRedirect(reverse('home'))
