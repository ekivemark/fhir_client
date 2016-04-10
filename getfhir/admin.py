from django import forms
from django.conf import settings
from django.contrib import admin

# Register your models here.

from .models import Session_State

class Session_StateAdmin(admin.ModelAdmin):
    """

    """
    # model = BBApplication
    list_display = ('state', 'auth',
                    'name' )
    search_fields = ('state', 'auth', 'name')


admin.site.register(Session_State, Session_StateAdmin)

