import json
import httplib

import requests
import requests.packages.urllib3.util
from django.conf import settings

BPM_URL = getattr(settings, 'BPM_URL', '') or 'http://127.0.0.1:7999'

__all__ = ['list_tasks', 'create_task', 'get_default_flowchart', 'get_task', 'set_task_context']


def list_tasks(task_class_name, date_created_ge=None, date_created_lt=None, context_eq=None):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'name_eq': task_class_name,
        'date_created_ge': date_created_ge.strftime('%s.%f') if date_created_ge else '',
        'date_created_lt': date_created_lt.strftime('%s.%f') if date_created_lt else ''
    }
    context_eq = context_eq or {}
    for key, value in context_eq.items():
        args['context_%s_eq' % key] = value
    response = requests.post(url, data=args)
    url = make_url_absolute(json.loads(response.content)['rel_tasks'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)['tasks']


def create_task(task_class_name, **exec_kwargs):
    url = make_url_absolute('/v1/tasks/%s/' % task_class_name)
    response = requests.get(url)
    assert httplib.OK == response.status_code
    form_create_task = json.loads(response.content)['form_create_task']
    http_call = getattr(requests, form_create_task['method'].lower())
    body = form_create_task['body']
    body['exec_kwargs'] = exec_kwargs
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_create_task['action'])
    response = http_call(url, data=body)
    return json.loads(response.content)

def set_task_context(task_id, key, value):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_set_context = json.loads(response.content)['form_set_context']
    http_call = getattr(requests, form_set_context['method'].lower())
    body = form_set_context['body']
    body['key'] = key
    body['value'] = value
    url = make_url_absolute(form_set_context['action'])
    response = http_call(url, data=body)
    return json.loads(response.content)

def get_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_task'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
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