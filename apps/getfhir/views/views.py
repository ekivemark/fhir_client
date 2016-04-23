from django.shortcuts import render

# Create your views here.

import base64

import codecs

import json

import requests
from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.http import (HttpResponse,
                         HttpResponseRedirect)
from django.core.urlresolvers import reverse
from django.shortcuts import (render_to_response,
                              RequestContext)

from django.views.decorators.csrf import csrf_exempt
from apps.getfhir.error import (ERROR_CODE,
                                kickout, )
from rauth import OAuth2Service

from _start.utils import (notNone,
                          Server_Name,
                          update_dict,
                          look_at_request)

from .state import (get_state,
                    create_state,
                    save_created_state,
                    is_valid_state,
                    save_code,
                    get_code,
                    save_tokens,
                    get_access,
                    get_refresh,
                    get_tokens,
                    )


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

SNOOP_URL = "localhost:8080/snoop"

SERVICE = OAuth2Service(name="CMS BlueButton FHIR",
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        access_token_url=TOKEN_URL,
                        #access_token_url=SNOOP_URL,
                        authorize_url=AUTH_URL,
                        #authorize_url=SNOOP_URL,
                        base_url=settings.OAUTH_TEST_INFO['BASE']
                        )


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

    # SERVICE = OAuth2Service(name="CMS BlueButton FHIR",
    #                         client_id=CLIENT_ID,
    #                         client_secret=CLIENT_SECRET,
    #                         access_token_url=TOKEN_URL,
    #                         authorize_url=AUTH_URL,
    #                         base_url=settings.OAUTH_TEST_INFO['BASE']
    # )

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

    params = {'client_id': CLIENT_ID,
              'redirect_uri': REDIRECT_URI,
              'state': state,
              'response_type': 'code',
              }

    url = SERVICE.get_authorize_url(**params)

    if settings.DEBUG:
        print("Authorization URL:", url)

    return HttpResponseRedirect(url)


def test_callback(request, *args, **kwargs):
    """
    OAuth Testing endpoint. Enter this as the Callback url

    """
    look_at_request(request)

    print("Request:", request)
    print("In the CallBack")
    
    code = request.GET['code']
    state = request.GET['state']

    context = OrderedDict()
    fmt = "json"
    if is_valid_state(state):

        context['template'] = "result.html"
        context['get_fmt'] = "json"
        context['display']  = "Me"
        context['code'] = code
        context['state'] = state
        context['ask'] = "/api/v1/me?_format=json"
        context['url'] = settings.OAUTH_TEST_INFO['BASE']

        result = save_code(state, code)
        context['return_to'] = Server_Name() + reverse('oauth2_fhir')
        context['goto']  = "a<href=/>Home</a>"

        data = {'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': REDIRECT_URI}


        #session = SERVICE.get_auth_session(data=data, decoder=json.loads)
        response = SERVICE.get_raw_access_token(data=data)

        look_at_request(response)
        get_text = response.json()

        if 'access_token' in get_text:
            print("got an access token")
            access = save_tokens(state,
                                 get_text['access_token'],
                                 get_text['refresh_token'])

        print("RESPONSE:", get_text)
        #RESPONSE: {"expires_in": 36000,
        #           "access_token": "h1vY5eDu69JKfV4nPpdu8xEan63hKl",
        #           "scope": "patient/*.read write_consent",
        #           "token_type": "Bearer",
        #           "refresh_token": "6HZnSwhfsGvfr9Aguw5n0e5CoGr8CQ"}

        response = response.json()
        session = SERVICE.get_session(response['access_token'])
        print("SESSION:", session)

        r = session.get(context['url']+context['ask'])

        convert = json.loads(r.text, object_pairs_hook=OrderedDict)

        content = OrderedDict(convert)
        if 'text' in content:
            context['text'] = content['text']
        context['content'] = json.dumps(content, indent=4)
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


def fhir_call(request):
    """
    :param request:
    :return:
    """

    # code = get_code(CLIENT_ID, AUTH_URL)
    #
    # url = settings.OAUTH_TEST_INFO['BASE']
    # url += "/fhir/Patient?_format=json"
    #
    # r = requests.get(url)

    fhir_ask = {
        # 'ask': "/fhir/Patient/1?_format=json",
        'ask': "/api/v1/Patient?_format=json",
        'name': "My Patient",
    }

    print("FHIR_ASK:", fhir_ask)
    fhir_call = fhir_request(request, fhir_ask)

    convert = json.loads(fhir_call['content'], object_pairs_hook=OrderedDict)

    content = OrderedDict(convert)
    context = {}
    context['template'] = "result.html"
    context['name'] = fhir_call['name']
    context['get_fmt'] = "json"
    context['pass_to'] = fhir_call['pass_to']
    context['content'] =  json.dumps(content, indent=4)

    return render_to_response(context['template'],
                              RequestContext(request,
                                             context))

    # return HttpResponse(json.dumps(content, indent=4),
    #                     content_type="application/%s" % "json")


def fhir_request(request, fhir_ask):
    """
    Generic Call to FHIR Server

    fhir_ask = {'CLIENT_ID': CLIENT_ID,
                'AUTH_URL': AUTH_URL,
                'template': "result.html",
                'ask': "/fhir/Patient?_format=json",
                'name': "FHIR Server Data",
                'format': "json",
                'url': settings.OAUTH_TEST_INFO['BASE'],
                }

    """

    fhir_call = {'CLIENT_ID': CLIENT_ID,
                 'AUTH_URL': AUTH_URL,
                 'template': "result.html",
                 'ask': "/fhir/Patient?_format=json",
                 'name': "FHIR Server Data",
                 'format': "json",
                 'headers': {'content-type': 'application/json',
                             'bearer': get_code(CLIENT_ID, AUTH_URL)},
                 'url': settings.OAUTH_TEST_INFO['BASE'],
                }

    if fhir_ask == None:
        return None

    # Overlay fhir_ask onto fhir_call
    for key, value in fhir_ask.items():
        fhir_call[key] = value

    if settings.DEBUG:
        print("Ask:", fhir_ask)
        print('Call:', fhir_call)

    # Get the current State value
    state = get_state(CLIENT_ID, AUTH_URL)
    code = get_code(fhir_call['CLIENT_ID'], fhir_call['AUTH_URL'])
    access = get_access(state)
    refresh = get_refresh(state)

    parms = {'client_id': CLIENT_ID,
              'redirect_uri': REDIRECT_URI,
              'client_secret': CLIENT_SECRET,
              # 'grant_type': 'authorization_code',
              'grant_type': 'refresh_token',
              'refresh_token': refresh,
              'state': state,
              'response_type': 'code',
             }

    data = {'refresh_token': refresh,'redirect_uri': REDIRECT_URI,
            'code': code,}

    # o = requests.post(TOKEN_URL, data=params, headers=fhir_call['headers'])
    # print("O:", o.text)

    # url = SERVICE.get_authorize_url(**params)

    if settings.DEBUG:
        print("Code:", code, "Accees:", access, "Refresh:", refresh)

    # data = {'code': code,
    #         'grant_type': 'authorization_code',
    #         'redirect_uri': REDIRECT_URI,
    #         'access_token': access,
    #         'refresh_token': refresh,
    #         }

    session = SERVICE.get_auth_session(data={'code':code,'redirect_uri':REDIRECT_URI})
    #session = SERVICE.get_raw_access_token('POST',**data)
    response = session.json()

    print("RESPONSE:", response)

    # r = session.get(fhir_call['url']+fhir_call['ask'], headers=fhir_call['headers'] )
    # session = SERVICE.get_session(response['access_token'])
    # print("Get:", r)

    pass_to = fhir_call['url']
    pass_to += fhir_call['ask']

    headers = fhir_call['headers']

    r = session.get(pass_to, headers=headers)

    if settings.DEBUG:
        print("R:", r)
        print(r.status_code)
        print(r.text)

    if r.status_code == 200:
        me = r.json()
        print("Me.json returned", me)
    else:

        msg = "Error %s: %s. [%s]" % (r.status_code,
                                      ERROR_CODE[r.status_code],
                                      pass_to)
        if settings.DEBUG:
            print(msg)
        messages.error(request, msg)
        return kickout(msg, format=fhir_call['format'], status_code=r.status_code)

    convert = json.loads(r.text, object_pairs_hook=OrderedDict)

    content = OrderedDict(convert)
    fhir_call['get_fmt'] = "json"
    fhir_call['pass_to'] = pass_to
    fhir_call['content'] = json.dumps(content, indent=4)

    return fhir_call


def home_index(request):
    """
    Home page

    :param request:
    :return:
    """

    context = {}
    # Breadcrumbs dicts are used in the include/breadcrumbs.html include within the
    # breadcrumb block
    # set livebreadcrumb and deadbreadcrumb to populate breadcrumbs at top of page.
    # deadbreadcrumb will just display a name with no active link. Use this for the current
    # active page
    # livebreadcrumb contains a dictionary of pages with links for breadcrumb page navigation
    # context['livebreadcrumb'] = {'Home': reverse('home'),}
    context['deadbreadcrumb'] = {'Home': reverse('home')}


    # context['me'] = get_remote_user(request)
    # print('context["me"]', context['me'])
    # if '401' in context['me']:
    #     print("we have an error")
    #     msg = build_message(request, context['me']['errors'])
    #
    #     messages.error(request, msg)
    #
    # if settings.DEBUG:
    #     print("ME:", context['me'])

    return render_to_response('index.html',
                              RequestContext(request, context, ))


def about(request):
    """
    About page

    :param request:
    :return:
    """

    context = {'api_target': settings.OAUTH_TEST_INFO['BASE']}
    context['livebreadcrumb'] = {'Home': reverse('home')}
    context['deadbreadcrumb'] = {'About': reverse('about')}

    return render_to_response('about.html',
                              RequestContext(request, context, ))


def get_remote_user(request):
    """
    Call Remote Server to get user data

    User name:  ekivemark
    first name: Mark
    last name:  Scrim
    email:      mark@ekivemark.com
    FHIR Id:    5636177

    :param request:
    :return:
    """

    if settings.DEBUG:
        print("Getting Remote User")
    me = {}

    me['url'] = settings.OAUTH_TEST_INFO['BASE']

    me['ask'] = "/api/v1/me" + "?_format=json"


    me = fhir_request(request, me)
    print("me...", me)
    if 'errors' and 'code' in me:
        msg = build_message(request,me['errors'])
        return kickout(msg, me['code'])

    return me


def build_message(request, errors):

    msg = []
    for m in errors:
        msg.append(m)
    if settings.DEBUG:
        print("Messages:", msg)
    messages.error(request, msg)

    return msg


def fhir_enquiry(request, context_override={}):
    """
    Building a generic enquiry using rauth
    :param request:
    :return:
    """

    state = get_state(CLIENT_ID,AUTH_URL)
    code = get_code(CLIENT_ID,AUTH_URL)

    # set default context
    context = {}
    context['template'] = "result.html"
    context['get_fmt'] = "json"
    context['display'] = "Me"
    context['code'] = code
    context['state'] = state
    context['ask'] = "/api/v1/me?_format=json"
    context['url'] = settings.OAUTH_TEST_INFO['BASE']
    context['headers'] = {'content-type': 'application/x-www-form-urlencoded',
                          'Authorization': "Bearer "+ get_code(CLIENT_ID, AUTH_URL)},

    # add / overwrite anything in context_override
    context = update_dict(context, context_override)

    data = {'code': code,
            'grant_type': 'authorization_code',
            'key': 'access_token',
            #'key': 'refresh_token',
            'access_token': get_access(state),
            'refresh_token': get_refresh(state),
            'redirect_uri': REDIRECT_URI}

    if settings.DEBUG:
        print("Context after update:", context)
        print("Data:", data)

    print("SERVICE:", SERVICE )

    # Get access_token
    headers = {}
    print('Context Headers:', dict(context['headers'][0]))
    #headers = {'headers': update_dict(headers, context_override=dict(context['headers'][0]))}
    headers = update_dict(headers, context_override=dict(context['headers'][0]))
    print("Headers:", headers)

    kw_to_send = {'data': data, 'headers': headers}

    #session = SERVICE.get_auth_session(method="POST",**kw_to_send)
    #session = SERVICE.get_session(get_access(state))
    #session = SERVICE.get_raw_access_token(method="POST", **kw_to_send)
    session = SERVICE.get_raw_access_token(data=data)

    #response = SERVICE.get_access_token(method="POST")
    # response = SERVICE.get_auth_session(data=data)
    print("Auth Session", session)
    #response = SERVICE.get_raw_access_token(data=data, **headers)

    get_text = session.json()

    if 'access_token' in get_text:
        print("got an access token")
        access = save_tokens(state,
                             get_text['access_token'],
                             get_text['refresh_token'])

    print("RESPONSE:", get_text)
    # RESPONSE: {"expires_in": 36000,
    #           "access_token": "h1vY5eDu69JKfV4nPpdu8xEan63hKl",
    #           "scope": "patient/*.read write_consent",
    #           "token_type": "Bearer",
    #           "refresh_token": "6HZnSwhfsGvfr9Aguw5n0e5CoGr8CQ"}


    sesn = SERVICE.get_session(get_text['access_token'])
    print("SESSION:", sesn)

    r = sesn.get(context['url'] + context['ask'])

    if settings.DEBUG:
        print("R:", r.content)

    return r


@csrf_exempt
def snooping(request):
    """"Use to see what is being sent to OAuth Server"""

    look_at_request(request)

    return HttpResponseRedirect("/")