from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.shortcuts import render

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^', include('bpm.webservice.urls')),
    url(r'^flowchart-demo/(?P<task_class_name>.*)/$',
        lambda x, task_class_name: render(x, 'flowchart_demo/auto_flow.html',
                                          {'task_class_name':task_class_name})),
)
