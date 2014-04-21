from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.shortcuts import render

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^butler/', include('bpm.contrib.butler.urls', namespace='butler', app_name='butler')),
    # url(r'^librarian/', include('bpm.contrib.librarian.urls', namespace='librarian', app_name='librarian')),
    url(r'^hub/', include('bpm.contrib.hub.urls', namespace='hub', app_name='hub')),
    url(r'^accounts/', include('bpm.contrib.auth.urls', namespace='accounts', app_name='accounts')),
    url(r'^service/', include('bpm.webservice.urls')),
    url(r'^', include('bpm.contrib.xinyun.urls', namespace='xinyun', app_name='xinyun')),
    url(r'^analysis/', include('bpm.contrib.analysis.urls', namespace='analysis', app_name='analysis')),
)
