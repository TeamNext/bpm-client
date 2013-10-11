from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.shortcuts import render

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^butler/', include('bpm.contrib.butler.urls', namespace='butler', app_name='butler')),
    url(r'^hub/', include('bpm.contrib.hub.urls', namespace='hub', app_name='hub')),
    url(r'^accounts/', include('bpm.contrib.auth.urls', namespace='accounts', app_name='accounts')),
    url(r'^', include('bpm.webservice.urls')),
)
