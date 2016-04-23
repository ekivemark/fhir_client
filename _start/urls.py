"""fhir_client URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse_lazy

from getfhir.views.access import (userlogin,
                                  fhir_patient,
                                  remote_logout)

from getfhir.views.views import (test_callback,
                                 fhir_service,
                                 fhir_call,
                                 home_index,
                                 about,
                                 snooping)

from getfhir.views.access import (connect, authorize)

urlpatterns = [
    url(r'^$', home_index, name='home'),
    url(r'^about$', about, name='about'),
    url(r'^oauth2_fhir$', fhir_service, name="oauth2_fhir"),
    # url(r'^o/endpoint/$', test_callback, name="oauth2_callback"),
    url(r'^o/endpoint/$', authorize, name="oauth2_callback"),

    url(r'^fhir$', fhir_call, name="fhir_call"),
    url(r'^fhir_patient$', fhir_patient, name="fhir_patient"),

    url(r'^connect$', connect, name="connect"),

    # Remote revoke token
    url(r'^remote_logout/$', remote_logout, name="remote_logout"),

    # login / logout
    url(r'^login$', login, name="login"),
    url(r'^logout$', logout, name="logout"),

    # Social-Auth
    # url('', include('social.apps.django_app.urls', namespace='social')),
    # admin
    url(r'^admin/', admin.site.urls),
    # Snooping on call
    url(r'^snoop$', snooping, name="snooping"),

]
