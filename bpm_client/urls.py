from django.conf.urls import patterns

urlpatterns = patterns(
    'bpm_client.views',
    (r'^flowchart/task-definition/(?P<task_class_name>.*)/$', 'task_definition_flow_chart'),
)
