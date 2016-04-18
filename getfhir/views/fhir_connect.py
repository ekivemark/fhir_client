#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
fhir_client
FILE: fhir_connect
Created: 4/16/16 3:38 PM

Based on
https://github.com/raphapassini/rauth_wrapper/blob/master/oauth_manager.py

"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json
import requests

from rauth import OAuth2Service

from django.conf import settings
from django.http import QueryDict

from .state import save_tokens, get_access, get_refresh, access_expired, get_tokens

class BaseConnect(object):
    session = None
    service = None

    def __init__(self, client_id, secret, name, authorize_url,
                 access_token_url, base_url):
        self.service = OAuth2Service(
            client_id=client_id,
            client_secret=secret,
            name=name,
            authorize_url=authorize_url,
            access_token_url=access_token_url,
            base_url=base_url)

    def get_authorize_url(self, **kwargs):
        if not kwargs.get('redirect_uri'):
            raise Exception('You must provide a redirect_uri to this function')

        return self.service.get_authorize_url(**kwargs)

    def get_session(self, code, state, redirect_uri, **kwargs):
        if self.session:
            return self.session

        kwargs.update({'code': code,
                       'grant_type': 'authorization_code',
                       'redirect_uri': redirect_uri})
        self.session = self.service.get_auth_session(data=kwargs, decoder=json.loads)
        return self.session

    def get_access_token(self, redirect_uri):
        return self.service.get_access_token(
            params={
                'redirect_uri': redirect_uri,
                # TODO: check the parameters
                # 'grant_type': 'client_credentials',
                'grant_type': 'authorization_code',
            })



class FHIRConnect(BaseConnect):
    """
    Flow to authenticate a user:
        - get_authorize_url()
        - Redirects user to this url, wait for callback and get the
          'code' param
        - get_session(code, redirect_uri)
     You'll endup with a rauth.session.OAuth2Session and you can use the
     api as this:
     # get the info about logedin user
     google_plus_connect.get_userinfo(session)
    """
    name = 'fhir_oauth2'
    authorize_url = settings.OAUTH_TEST_INFO['AUTH_URL']
    access_token_url = settings.OAUTH_TEST_INFO['TOKEN_URL']
    base_url = settings.OAUTH_TEST_INFO['BASE']

    def __init__(self, client_id, secret):
        super(FHIRConnect, self).__init__(
            client_id=client_id,
            secret=secret,
            name=self.name,
            authorize_url=self.authorize_url,
            access_token_url=self.access_token_url,
            base_url=self.base_url)


    def get_session(self, code, state, redirect_uri, *args, **kwargs):
        kwargs.update({
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.service.client_id,
            'client_secret': self.service.client_secret,
            'grant_type': 'authorization_code',

        })
        response = self.service.get_raw_access_token(data=kwargs)
        if settings.DEBUG:
            print("get_session_response:", response.text)
        response = response.json()
        if settings.DEBUG:
            print("response.get", response)
        if 'error' in response:
            if settings.DEBUG:
                print("there was an error in get_session:", response['error'])
            kwargs.update({'refresh_token': get_refresh(state),
                           'grant_type': 'refresh_token',})
            response = self.service.get_raw_access_token(data=kwargs)
            response = response.json()
            refresh = response['refresh_token']
            access = response['access_token']
            save_tokens(state, access, refresh)
            kwargs.update({'refresh_token': refresh,
                           'access_token': access})

            if settings.DEBUG:
                print("kwargs updated to:", kwargs)
                print("Refresh failed:", response)
        else:
            #  {"access_token": "2okmtZQBDAh070Xh9ftoK10EQsdWnK",
            #   "token_type": "Bearer",
            #   "expires_in": 36000,
            #   "refresh_token": "9nCKlbslEuHJUdtz42byFoEd7aUQW1",
            #   "scope": "patient/*.read write_consent"}
            if 'refresh_token' in response:
                refresh = response['refresh_token']
                access = response['access_token']
                save_tokens(state, access, refresh)
                print('Saved Access and Refresh Tokens')
                kwargs.update({'refresh_token': refresh,
                               'access_token': access})

        if settings.DEBUG:
            print("response is now:", response)
            print('Check for X-Frame-Options:', response.get('X-Frame-Options') )
            print("Kwargs:", kwargs)

        # return self.service.get_auth_session(**kwargs)

        return self.service.get_session(response['access_token'])


    def get_userinfo(self, session):
        if not type(session) == 'rauth.session.OAuth2Session':
            raise Exception('Expect rauth.session.OAuth2Session object '
                            'instead got a %s' % (type(session)))
        return session.get(
            self.base_url + "/api/v1/me?_format=json" )


    def get_a_session(self, code, state, redirect_uri, *args, **kwargs):
        """Using requests directly to handle OAuth 2.0 calls"""

        kwargs.update({
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.service.client_id,
            'client_secret': self.service.client_secret,
            'grant_type': 'authorization_code',
        })

        print("KWARGS in get_a_session:", kwargs)

        payload = {'redirect_uri': redirect_uri,
                   'grant_type': 'authorization_code',
                   'client_id': self.service.client_id,
                   'client_secret': self.service.client_secret,
                   'code': code,
                   'state': state
        }

        headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Authorization': 'Bearer ' + code }

        r = requests.post(self.access_token_url, data=payload, headers=headers)
        if settings.DEBUG:
            print("R.headers:", r.headers)
            print("R.text:", r.text)

        content = r.json()
        if "expires" in content:
            access = save_tokens(state,
                                 content['access_token'],
                                 content['refresh_token'],
                                 content['expires'])

        return r


    def oauth_access(self, code, state, redirect_uri, url, method="GET", *args, **kwargs):
        """ Make a call using an OAuth protected API
            check if access_token has expired
            if yes - renew with a refresh_token call
        """
        if settings.DEBUG:
            print("Using State:", state)
        if access_expired(state):
            # renew tokens
            print("Expired -so renew")
            tokens = get_tokens(state)

            if settings.DEBUG:
                print("Working with tokens:" , tokens)

            payload = {#'redirect_uri': redirect_uri,
                       'grant_type': 'refresh_token',
                       'client_id': self.service.client_id,
                       'client_secret': self.service.client_secret,
                       #'code': code,
                       #'state': state,
                       'refresh_token': tokens['refresh_token']
                       }
            if settings.DEBUG:
                print("Sending:", payload)

            headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
                       'Authorization': 'Bearer ' + code}

            r = requests.post(self.access_token_url, data=payload, headers=headers)
            print('We got r back: ', r.text)
            # make call to renew tokens
            if 'access_token' in r.text:
                result = r.json()
                save_tokens(state,
                            result['access_token'],
                            result['refresh_token'],
                            result['expires'])
            # update tokens
            tokens = get_tokens(state)


        payload = {'grant_type': 'authorization_code',
                   'client_id': self.service.client_id,
                   'client_secret': self.service.client_secret,
                   'code': code,
                   'state': state
                  }
        headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Authorization': 'Bearer ' + code}

        called_url = self.base_url + url
        # build call to api

        # make call
        r = requests.get(called_url, data=payload, headers=headers)
        # return result of call
        if settings.DEBUG:
            print("Result of call:", r.text)

        #result = r.json()

        return r

    def renew_tokens(self, code, state, tokens):
        """Renew the access_token"""

        payload = {  # 'redirect_uri': redirect_uri,
            'grant_type': 'refresh_token',
            'client_id': settings.OAUTH_TEST_INFO['CLIENT_ID'],
            'client_secret': settings.OAUTH_TEST_INFO['CLIENT_SECRET'],
            # 'code': code,
            # 'state': state,
            'refresh_token': tokens['refresh_token']
        }

        if settings.DEBUG:
            print("Sending:", payload)

        headers = {'content_type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   #'Authorization': 'Bearer ' + code}
                   'Authorization': 'Bearer ' + code}

        r = requests.post(self.access_token_url+"?code="+code+"&state="+state, data=payload, headers=headers)

        if settings.DEBUG:
            print('We got r back: ', r.text)
            print('With header:', r.headers)

        # make call to renew tokens
        if 'access_token' in r.text:
            result = r.json()
            save_tokens(state,
                    result['access_token'],
                    result['refresh_token'],
                    result['expires'])
       # update tokens
        tokens = get_tokens(state)

        return tokens