import json
import httplib

import requests
import requests.packages.urllib3.util
from django.conf import settings

BPM_URL = getattr(settings, 'BPM_URL', '') or 'http://127.0.0.1:7999'

__all__ = ['list_tasks', 'start_task', 'create_task', 'get_task_definition_flowchart', 'get_task', 'get_task_trace',
           'set_task_context', 'suspend_task', 'resume_task', 'revoke_task', 'retry_task', 'get_task_log',
           'callback_task', 'list_task_waiting_event_names']


def list_tasks(name_eq=None, date_created_ge=None, date_created_lt=None, context_eq=None):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'name_eq': name_eq or '',
        'date_created_ge': date_created_ge.strftime('%s.%f') if date_created_ge else '',
        'date_created_lt': date_created_lt.strftime('%s.%f') if date_created_lt else ''
    }
    context_eq = context_eq or {}
    for key, value in context_eq.items():
        args['context_%s_eq' % key] = value
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_tasks'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def start_task(task_definition_name, *exec_args, **exec_kwargs):
    return create_task(task_definition_name, *exec_args, **exec_kwargs).start()


def create_task(task_definition_name, *exec_args, **exec_kwargs):
    return TaskBuilder(task_definition_name, exec_args, exec_kwargs)


class TaskBuilder(object):
    def __init__(self, task_definition_name, args, kwargs):
        self.task_definition_name = task_definition_name
        self.args = args
        self.kwargs = kwargs
        self._context = {}

    def context(self, context):
        task_builder = self
        for key, value in context.items():
            task_builder = getattr(task_builder, key)(value)
        return task_builder

    def __getattr__(self, item):
        def set_context(value):
            self._context[item] = value
            return self

        return set_context

    def start_later(self):
        return self.start(start_later=True)

    def start(self, start_later=False):
        url = make_url_absolute('/v1/search/')
        args = {
            'searching_type': 'task',
            'name_eq': self.task_definition_name
        }
        response = requests.post(url, data=args)
        assert httplib.OK == response.status_code
        form_create_task = json.loads(response.content)['form_create_task']
        http_call = getattr(requests, form_create_task['method'].lower())
        body = form_create_task['body']
        body['exec_args'] = self.args
        body['exec_kwargs'] = self.kwargs
        body['context'] = self._context
        body['start_later'] = start_later
        body = {k: json.dumps(v) for k, v in body.items()}
        url = make_url_absolute(form_create_task['action'])
        response = http_call(url, data=body)
        assert httplib.OK == response.status_code
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
    return response.content

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

def get_task_trace(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_task_trace'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def get_task_log(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_task_log'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def list_task_waiting_event_names(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_task_waiting_event_names'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def get_task_definition_flowchart(task_definition_name, *args, **kwargs):
    url = make_url_absolute('/v1/search/')
    response = requests.post(url, data={'searching_type': 'task-definition', 'name_eq': task_definition_name})
    assert httplib.OK == response.status_code
    if args or kwargs:
        form_custom_flowchart = json.loads(response.content)['form_custom_flowchart']
        http_call = getattr(requests, form_custom_flowchart['method'].lower())
        body = form_custom_flowchart['body']
        body['exec_args'] = json.dumps(args)
        body['exec_kwargs'] = json.dumps(kwargs)
        url = make_url_absolute(form_custom_flowchart['action'])
        response = http_call(url, data=body)
        assert httplib.OK == response.status_code
        return json.loads(response.content)
    else:
        rel_default_flowchart = make_url_absolute(json.loads(response.content)['rel_default_flowchart'])
        response = requests.get(rel_default_flowchart)
        assert httplib.OK == response.status_code
        return json.loads(response.content)


def suspend_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_suspend = json.loads(response.content)['form_suspend']
    http_call = getattr(requests, form_suspend['method'].lower())
    body = form_suspend['body']
    url = make_url_absolute(form_suspend['action'])
    response = http_call(url, data=body)
    return response.content


def resume_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_resume = json.loads(response.content)['form_resume']
    http_call = getattr(requests, form_resume['method'].lower())
    body = form_resume['body']
    url = make_url_absolute(form_resume['action'])
    response = http_call(url, data=body)
    return response.content


def revoke_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_revoke = json.loads(response.content)['form_revoke']
    http_call = getattr(requests, form_revoke['method'].lower())
    body = form_revoke['body']
    url = make_url_absolute(form_revoke['action'])
    response = http_call(url, data=body)
    return response.content


def retry_task(task_id, *exec_args, **exec_kwargs):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_retry = json.loads(response.content)['form_retry']
    http_call = getattr(requests, form_retry['method'].lower())
    body = form_retry['body']
    body['exec_args'] = exec_args
    body['exec_kwargs'] = exec_kwargs
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_retry['action'])
    response = http_call(url, data=body)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


def complete_failed_task(task_id, data, ex_data, return_code, exec_args=None, exec_kwargs=None):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_retry = json.loads(response.content)['form_retry']
    http_call = getattr(requests, form_retry['method'].lower())
    body = form_retry['body']
    body['exec_args'] = exec_args
    body['exec_kwargs'] = exec_kwargs
    body['return_value'] = {
        'data': data,
        'ex_data': ex_data,
        'return_code': return_code
    }
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_retry['action'])
    response = http_call(url, data=body)
    return json.loads(response.content)


def callback_task(task_id, event_name, event_data):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_retry = json.loads(response.content)['form_callback']
    http_call = getattr(requests, form_retry['method'].lower())
    body = form_retry['body']
    body['event_name'] = event_name
    body['event_data'] = json.dumps(event_data)
    url = make_url_absolute(form_retry['action'])
    response = http_call(url, data=body)
    return response.content


def make_url_absolute(url):
    scheme, auth, host, port, path, query, fragment = requests.packages.urllib3.util.parse_url(url)
    if not scheme:
        return '%s%s' % (BPM_URL, url)
    else:
        return url