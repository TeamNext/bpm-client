# -*- coding:utf-8 -*-
import json
import urllib
import httplib
import logging

import requests
import requests.packages.urllib3.util
from django.conf import settings

BPM_SERVICE_URL = getattr(settings, 'BPM_URL', 'http://stage.xy.ied.com') + '/service'

__version__ = '1.2.4'

__all__ = ['list_tasks', 'start_task', 'create_task', 'get_task_definition_flowchart', 'get_task', 'get_task_trace',
           'set_task_context', 'suspend_task', 'resume_task', 'revoke_task', 'retry_task', 'get_task_log',
           'callback_task', 'list_task_waiting_event_names', 'list_task_tries', 'change_task_step_args',
           'create_task_schedule', 'list_task_schedules',
           'get_task_schedule', 'delete_task_schedule']

LOGGER = logging.getLogger(__name__)

# 获取任务列表（根据任务名，日期，context来搜索）
def list_tasks(name_eq, date_created_ge=None, date_created_lt=None, context_eq=None):
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


# 直接创建并开始一个任务，返回值即为新创建的任务
def start_task(task_definition_name, task_info, *exec_args, **exec_kwargs):
    return create_task(task_definition_name, task_info, *exec_args, **exec_kwargs).start()


# 返回一个TaskBuilder对象， 能设置bpm_context然后开始执行
# 如果你需要的是直接创建并开始一个任务，换用start_task方法
def create_task(task_definition_name, task_info, *exec_args, **exec_kwargs):
    return TaskBuilder(task_definition_name, task_info, *exec_args, **exec_kwargs)


# 用于创建一个task，并设置其context， 然后再开始执行
# info_data: app, cc_biz_id, operator, operate_type, origin, operators=None, title=None, ticket=None, 
class TaskBuilder(object):
    def __init__(self, task_definition_name, task_info, *exec_args, **exec_kwargs):
        self.task_definition_name = task_definition_name
        self.args = exec_args
        self.kwargs = exec_kwargs
        self._context = {}
        self.task_info = task_info


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
        body['task_info'] = self.task_info
        body['context'] = self._context
        body['start_later'] = start_later

        body = {k: json.dumps(v) for k, v in body.items()}
        url = make_url_absolute(form_create_task['action'])
        response = http_call(url, data=body)
        if httplib.OK != response.status_code:
            # LOGGER.error(response)
            print response.status_code, response.content
        assert httplib.OK == response.status_code
        return json.loads(response.content)


# 设置任务的全局变量
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

# 改变任务步骤的参数
def change_task_step_args(task_id, step_name, step_args):
    url = make_url_absolute('/v1/search')
    args = {
        'searching_type': 'task-step',
        'task_id_eq': task_id,
        'step_name_eq': step_name
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_change_args = json.loads(response.content)['form_change_args']
    http_call = getattr(requests, form_change_args['method'].lower())
    body = form_change_args['body']
    body['args'] = step_args
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_change_args['action'])
    response = http_call(url, data=body)
    return response.content


# 获取单个任务的概要信息
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


# 获取单个任务的完整执行信息
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


# 获取任务的执行日志
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


# 获取任务正在等待的事件列表
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

# 获取任务的重试记录
def list_task_tries(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_task_tries'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


# 获取任务定义的流程图数据
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


# 暂停一个任务
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


# 恢复执行
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


# 撤销任务
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


# 重试任务
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


# 强制完成失败的任务
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


# 通用回调(唤醒一个事件)
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


#添加一个定时任务
def create_task_schedule(name, task_info, task_args, creator, crontab, next_time):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_add_task_schedule = json.loads(response.content)['form_create_task_schedule']
    http_call = getattr(requests, form_add_task_schedule['method'].lower())
    body = form_add_task_schedule['body']
    if isinstance(task_args, dict):
        task_args = json.dumps(task_args)
    body['name'] = name
    body['kwargs'] = task_args
    body['creator'] = creator
    body['crontab'] = crontab
    body['time'] = next_time
    body['app'] = task_info.get('app', '')
    body['cc_biz_id'] = task_info.get('cc_biz_id', '')
    body['operator'] = task_info.get('operator', '')
    body['operators'] = task_info.get('operators', '')
    body['title'] = task_info.get('title', '')
    body['operate_type'] = task_info.get('operate_type', '')
    url = make_url_absolute(form_add_task_schedule['action'])
    response = http_call(url, data=body)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


#获取指定创建者的所有定时任务
def list_task_schedules(creator):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'creator': creator,
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_list_task_schedules'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


#根据schedule_id获取定时任务
def get_task_schedule(schedule_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'schedule_id': schedule_id
    }
    response = requests.post(url, args)
    assert httplib.OK == response.status_code
    url = make_url_absolute(json.loads(response.content)['rel_get_task_schedule'])
    response = requests.get(url)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


#根据schedule_id删除指定的定时任务, schedule_id由list_task_scheduls获取
def delete_task_schedule(schedule_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'schedule_id': schedule_id
    }
    response = requests.post(url, data=args)
    assert httplib.OK == response.status_code
    form_del_task_schedule = json.loads(response.content)['form_delete_task_schedule']
    http_call = getattr(requests, form_del_task_schedule['method'].lower())
    body = form_del_task_schedule['body']
    url = make_url_absolute(form_del_task_schedule['action'])
    response = http_call(url, data=body)
    assert httplib.OK == response.status_code
    return json.loads(response.content)


# 内部方法：对芯雲接口服务url的封装
def make_url_absolute(url, base_url = BPM_SERVICE_URL):
    scheme, auth, host, port, path, query, fragment = requests.packages.urllib3.util.parse_url(url)
    if not scheme:
        return '%s%s' % (base_url, url)
    else:
        return url
