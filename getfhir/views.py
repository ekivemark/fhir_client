from django.shortcuts import render

# Create your views here.

import base64

import codecs

import json
import oauth2 as oauth
import requests
import urllib

from base64 import b64encode
from collections import OrderedDict

from http.client import HTTPSConnection
from httplib2 import BasicAuthentication

from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseRedirect)
from django.core.urlresolvers import reverse
from django.shortcuts import (render_to_response,
                              RequestContext)

from rauth import OAuth2Service
from uuid import uuid4

from _start.utils import notNone, Server_Name
from .auth import set_Basic_Auth_Header
from .models import Session_State


# OAUTH_TEST_INFO = {'CLIENT_ID': "HDHZqA7dEnAif9PRq1atwWXMtkZNXUtZodb93iH0",
#                    'CLIENT_SECRET': "H4BIyuyGTBTVG9CvVFtcMhYYIS4xQScbsYtaREEcYHN1VsIf4MeWjxYC56dqc970ACDnf5A1Kge6rVz5yecaTJjlORv502XLIcKlO5JwX2bAsw5bSXFdsjtsXVbX7ScE",
#                    'USER': "healthcamp_mark",
#                    'CLIENT_TYPE': "confidential",
#                    'GRANT_TYPE': "authorization_code",
#                    'NAME': "First_Test",
#                    'REDIRECT_URI': "http://localhost:8080/o/endpoint/",
#                    # 'URL': "https://api.bbonfhir.com/o/token",
#                    'AUTH_URL': "https://api.bbonfhir.com/o/authorize",
#                    'TOKEN_URL': "https://api.bbonfhir.com/o/token",
#                    'BASE': "https://api.bbonfhir.com",
#                    }

REDIRECT_URI = settings.OAUTH_TEST_INFO['REDIRECT_URI']
CLIENT_ID = settings.OAUTH_TEST_INFO['CLIENT_ID']
CLIENT_SECRET = settings.OAUTH_TEST_INFO['CLIENT_SECRET']
TOKEN_URL = settings.OAUTH_TEST_INFO['TOKEN_URL']
AUTH_URL = settings.OAUTH_TEST_INFO['AUTH_URL']


def fhir_service(request):
    """
    Test OAuth 2.0 access using rauth

       service = OAuth2Service(
                   name='example',
                   client_id='123',
                   client_secret='456',
                   access_token_url='https://example.com/token',
                   authorize_url='https://example.com/authorize',
                   base_url='https://example.com/api/')

    Given the simplicity of OAuth 2.0 now this object `service` can be used to
    retrieve an authenticated session in two simple steps::

        # the return URL is used to validate the request
        params = {'redirect_uri': 'http://example.com/',
                  'response_type': 'code'}
        url = service.get_authorize_url(**params)

        # once the above URL is consumed by a client we can ask for an access
        # token. note that the code is retrieved from the redirect URL above,
        # as set by the provider
        data = {'code': 'foobar',
                'grant_type': 'authorization_code',
                'redirect_uri': 'http://example.com/'}

        session = service.get_auth_session(data=data)


    # https://api.bbonfhir.com/o/authorize?state=random_state_string
    # &client_id=HDHZqA7dEnAif9PRq1atwWXMtkZNXUtZodb93iH0&response_type=code

    # Authorization goes here:

    # http://localhost:8080/o/endpoint/?code=9GIdEZI7B0GxYMU5mPhKz4rCg6Nhv6
    # &state=random_state_string


    """

    SERVICE = OAuth2Service(name="CMS BlueButton FHIR",
                            client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            access_token_url=TOKEN_URL,
                            authorize_url=AUTH_URL,
                            base_url=settings.OAUTH_TEST_INFO['BASE']
    )

    # service = OAuth2Service(
    #     name="CMS BlueButton FHIR",
    #     client_id=CLIENT_ID,
    #     client_secret=CLIENT_SECRET,
    #     access_token_url=TOKEN_URL,
    #     authorize_url=AUTH_URL,
    #     base_url=settings.OAUTH_TEST_INFO['BASE']
    # )

    # code = uuid4()
    # raw = service.get_raw_access_token()
    # if settings.DEBUG:
    #     print("Raw:", raw)
    state = create_state()

    params = {'redirect_uri': REDIRECT_URI,
          'state': state,
          'response_type': 'code'}

    url = SERVICE.get_authorize_url(**params)

    if settings.DEBUG:
        print("Authorization URL:", url)

    return HttpResponseRedirect(url)


def test_callback(request, *args, **kwargs):
    """
    OAuth Testing endpoint. Enter this as the Callback url

    """

    print("Request:", request)
    
    code = request.GET['code']
    state = request.GET['state']

    context = OrderedDict()
    fmt = "json"
    if is_valid_state(state):

        context['template'] = "result.html"
        context['get_fmt'] = "json"
        context['display']  = "Patient"
        context['code'] = code
        context['state'] = state

        result = save_code(state, code)
        context['return_to'] = Server_Name() + reverse('oauth2_fhir')
        context['goto']  = "a<href=/>Home</a>"

        # data = dict(code=code, redirect_uri=REDIRECT_URI)
        # session = SERVICE.get_auth_session()
        #
        # if settings.DEBUG:
        #     print("Session:", session)
        # context['session'] = session

        return render_to_response(context['template'],
                                  RequestContext(request,
                                                 context))
        # return HttpResponse(json.dumps(context, indent=4),
        #                     content_type="application/%s" % fmt)
    else:
        context['error'] = "Error: Invalid state"
        context['state'] = state
        context['goto']  = "a<href=/>Home</a>"

        return HttpResponse(json.dumps(context, indent=4),
                            content_type="application/%s" % fmt)


def create_state():

    state_save = {'state': uuid4().urn[9:],'AUTH_URL': AUTH_URL,'CLIENT': CLIENT_ID}

    print("State to save:", state_save)
    saved = save_created_state(state_save)
    print("SAved:", saved)

    print("Returned State:", state_save)
    return state_save['state']


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


def fhir_call(request):
    """
    :param request:
    :return:
    """

    code = get_code(CLIENT_ID, AUTH_URL)

    url = settings.OAUTH_TEST_INFO['BASE']
    url += "/fhir/Patient?_format=json"

    r = requests.get(url)

    convert = json.loads(r.text, object_pairs_hook=OrderedDict)

    content = OrderedDict(convert)
    context = {}
    context['template'] = "result.html"
    context['get_fmt'] = "json"
    context['pass_to'] = url
    context['content'] =  json.dumps(content, indent=4)

    return render_to_response(context['template'],
                              RequestContext(request,
                                             context))

    # return HttpResponse(json.dumps(content, indent=4),
    #                     content_type="application/%s" % "json")


def home_index(request):
    """
    Home page
    :param request:
    :return:
    """

    context = {}
    user = request.user

    return render_to_response('index.html',
                              RequestContext(request, context, ))

