import json
import httplib

import requests
import requests.packages.urllib3.util
from django.conf import settings

BPM_URL = getattr(settings, 'BPM_URL', '') or 'http://127.0.0.1:7999'

__all__ = ['list_tasks', 'create_task', 'get_default_flowchart']


def list_tasks(task_class_name, date_created_ge=None, date_created_lt=None):
    url = make_url_absolute('/v1/search/')
    response = requests.post(url, data={
        'searching_type': 'task',
        'name_eq': task_class_name,
        'date_created_ge': date_created_ge.strftime('%s.%f') if date_created_ge else '',
        'date_created_lt': date_created_lt.strftime('%s.%f') if date_created_lt else ''
    })
    url = make_url_absolute(json.loads(response.content)['rel_tasks'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)['tasks']


def create_task(task_class_name, **exec_kwargs):
    url = make_url_absolute('/v1/tasks/%s/' % task_class_name)
    response = requests.get(url)
    form_create_task = json.loads(response.content)['form_create_task']
    http_call = getattr(requests, form_create_task['method'].lower())
    body = form_create_task['body']
    body['exec_kwargs'] = exec_kwargs
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_create_task['action'])
    response = http_call(url, data=body)
    return json.loads(response.content)


def get_default_flowchart(task_class_name):
    url = make_url_absolute('/v1/search/')
    response = requests.post(url, data={'searching_type': 'task-definition', 'name_eq': task_class_name})
    rel_default_flowchart = make_url_absolute(json.loads(response.content)['rel_default_flowchart'])
    response = requests.get(rel_default_flowchart)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def make_url_absolute(url):
    scheme, auth, host, port, path, query, fragment = requests.packages.urllib3.util.parse_url(url)
    if not scheme:
        return '%s%s' % (BPM_URL, url)
    else:
        return url