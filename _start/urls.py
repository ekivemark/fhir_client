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
from django.conf.urls import url
from django.contrib import admin

from getfhir.views import (test_callback,
                           fhir_service)

urlpatterns = [
    url(r'^oauth2_fhir$', fhir_service, name="oauth2_fhir"),
    url(r'^o/endpoint/$', test_callback, name="oauth2_callback"),

    # admin
    url(r'^admin/', admin.site.urls),

]
