#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import httplib
import logging
import datetime
import time

import requests
import requests.packages.urllib3.util
import uuid
try:
    from django.conf import settings
    if settings.RUN_MODE == 'PRODUCT':
        BPM_URL = 'http://xy.ied.com'
    else:
        BPM_URL = 'http://stage.xy.ied.com'
    # BPM_SERVICE_URL = BPM_URL + '/service'
    BPM_SERVICE_URL = BPM_URL + '/service'
except:
    # if '__main__' != __name__:
    #     raise
    # BPM_URL = None
    # BPM_SERVICE_URL = None
    BPM_URL = 'http://stage.xy.ied.com'
    BPM_SERVICE_URL = BPM_URL + '/service'

__version__ = '1.3.6'

__all__ = ['list_tasks', 'start_task', 'create_task', 'start_auth_task', 'create_auth_task',
           'get_task_definition_flowchart', 'get_task', 'get_task_trace',
           'set_task_context', 'suspend_task', 'resume_task', 'revoke_task', 'retry_task', 'get_task_log',
           'callback_task', 'list_task_waiting_event_names', 'list_task_tries', 'change_task_step_args',
           'create_task_schedule', 'list_task_schedules', 'get_task_schedule', 'delete_task_schedule',
           'get_tasks_by_schedule', 'get_task_context', 'complete_failed_task', 'failure_task']

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
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_tasks'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 直接创建并开始一个任务，返回值即为新创建的任务(混合云版)
# task_info中需要包含app_code, app_secret, auth_token三个参数
def start_auth_task(task_definition_name, task_info, *exec_args, **exec_kwargs):
    return create_auth_task(task_definition_name, task_info, *exec_args, **exec_kwargs).start()


# 直接创建并开始一个任务，返回值即为新创建的任务
def start_task(task_definition_name, task_info, *exec_args, **exec_kwargs):
    return create_task(task_definition_name, task_info, *exec_args, **exec_kwargs).start()


# 返回一个TaskBuilder对象， 能设置bpm_context然后开始执行(混合云版)
def create_auth_task(task_definition_name, task_info, *exec_args, **exec_kwargs):
    app_code = task_info.get('app')
    app_secret = task_info.get('app_secret')
    auth_token = task_info.get('auth_token')
    assert app_code
    assert app_secret
    assert auth_token
    del task_info['app_code']
    del task_info['app_secret']
    del task_info['auth_token']
    return create_task(
            task_definition_name,
            task_info,
            *exec_args,
            **exec_kwargs
            ).app_code(app_code).app_secret(app_secret).auth_token(auth_token)


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

    def start_debug(self):
        return self.start(debug=True)

    def start_later(self):
        return self.start(start_later=True)

    def start(self, start_later=False, debug=False):
        url = make_url_absolute('/v1/search/')
        args = {
            'searching_type': 'task',
            'name_eq': self.task_definition_name
        }
        response = requests.post(url, data=args)
        assert_http_call_is_successful(response)
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
        response = http_call(url, data=body, headers={"X-RANDOM-TOKEN": uuid.uuid1().get_hex()})
        assert_http_call_is_successful(response)

        # 用本地浏览器打开任务流程页
        retval = json.loads(response.content)
        task_id = retval.get('id')
        if task_id and debug:
            import webbrowser
            webbrowser.open('{}/butler/task/{}/flowchart/'.format(BPM_URL, task_id))
        return retval


# 设置任务的全局变量
def set_task_context(task_id, key, value):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_set_context = json.loads(response.content)['form_set_context']
    http_call = getattr(requests, form_set_context['method'].lower())
    body = form_set_context['body']
    body['key'] = key
    body['value'] = value
    url = make_url_absolute(form_set_context['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content

# 获取任务的全局变量
def get_task_context(task_id, key):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-context',
        'id_eq': task_id,
        'key': key
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_get_task_context'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 改变任务步骤的参数
def change_task_step_args(task_id, step_name, step_args):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-step',
        'task_id_eq': task_id,
        'step_name_eq': step_name
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_change_args = json.loads(response.content)['form_change_args']
    http_call = getattr(requests, form_change_args['method'].lower())
    body = form_change_args['body']
    body['args'] = step_args
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_change_args['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


# 获取单个任务的概要信息
def get_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_task'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 获取单个任务的完整执行信息
def get_task_trace(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_task_trace'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 获取任务的执行日志
def get_task_log(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_task_log'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 获取任务正在等待的事件列表
def list_task_waiting_event_names(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_task_waiting_event_names'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)

# 获取任务的重试记录
def list_task_tries(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_task_tries'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 获取任务定义的流程图数据
def get_task_definition_flowchart(task_definition_name, *args, **kwargs):
    url = make_url_absolute('/v1/search/')
    response = requests.post(url, data={'searching_type': 'task-definition', 'name_eq': task_definition_name})
    assert_http_call_is_successful(response)
    if args or kwargs:
        form_custom_flowchart = json.loads(response.content)['form_custom_flowchart']
        http_call = getattr(requests, form_custom_flowchart['method'].lower())
        body = form_custom_flowchart['body']
        body['exec_args'] = json.dumps(args)
        body['exec_kwargs'] = json.dumps(kwargs)
        url = make_url_absolute(form_custom_flowchart['action'])
        response = http_call(url, data=body)
        assert_http_call_is_successful(response)
        return json.loads(response.content)
    else:
        rel_default_flowchart = make_url_absolute(json.loads(response.content)['rel_default_flowchart'])
        response = requests.get(rel_default_flowchart)
        assert_http_call_is_successful(response)
        return json.loads(response.content)


# 暂停一个任务
def suspend_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_suspend = json.loads(response.content)['form_suspend']
    http_call = getattr(requests, form_suspend['method'].lower())
    body = form_suspend['body']
    url = make_url_absolute(form_suspend['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


# 恢复执行
def resume_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_resume = json.loads(response.content)['form_resume']
    http_call = getattr(requests, form_resume['method'].lower())
    body = form_resume['body']
    url = make_url_absolute(form_resume['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


# 撤销任务
def revoke_task(task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_revoke = json.loads(response.content)['form_revoke']
    http_call = getattr(requests, form_revoke['method'].lower())
    body = form_revoke['body']
    url = make_url_absolute(form_revoke['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


# 重试任务
def retry_task(xy_task_id, *exec_args, **exec_kwargs):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': xy_task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_retry = json.loads(response.content)['form_retry']
    http_call = getattr(requests, form_retry['method'].lower())
    body = form_retry['body']
    body['exec_args'] = exec_args
    body['exec_kwargs'] = exec_kwargs
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_retry['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 任务强制失败
def failure_task(xy_task_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': xy_task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_failure = json.loads(response.content)['form_failure']
    http_call = getattr(requests, form_failure['method'].lower())
    body = form_failure['body']
    body['exec_args'] = exec_args
    body['exec_kwargs'] = exec_kwargs
    body = {k: json.dumps(v) for k, v in body.items()}
    url = make_url_absolute(form_failure['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


# 强制完成失败的任务
def complete_failed_task(xy_task_id, data, ex_data, return_code, exec_args=None, exec_kwargs=None):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': xy_task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
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
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 通用回调(唤醒一个事件)
def callback_task(task_id, event_name, event_data):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task',
        'id_eq': task_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_retry = json.loads(response.content)['form_callback']
    http_call = getattr(requests, form_retry['method'].lower())
    body = form_retry['body']
    body['event_name'] = event_name
    body['event_data'] = json.dumps(event_data)
    url = make_url_absolute(form_retry['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return response.content


#添加一个定时任务
def create_task_schedule(name, task_info, task_args, creator, crontab, next_time):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
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
    assert_http_call_is_successful(response)
    _add_mention(name, task_info, creator, next_time, url)
    return json.loads(response.content)


def _add_mention(name, task_info, creator, next_time, url):
    mentions = task_info.get('mentions', None)
    if not mentions:
        return
    time_list = mentions.split(";")
    time_format = "%Y-%m-%d %H:%M:%S"
    for m_time in time_list:
        mention_dt = datetime.datetime.strptime(next_time, time_format) - datetime.timedelta(minutes=int(m_time))
        mention_time = datetime.datetime.strftime(mention_dt, time_format)
        message = u"你关注的芯雲定时任务%s, 将于%s开始执行" % (name, next_time)

        #wechat_send
        body = {}
        body['name'] = "bk.smcs.wechat_send"
        body['kwargs'] = json.dumps({'receivers': task_info.get('operators'),
                'message':message})
        body['creator'] = creator
        body['crontab'] = ""
        body['time'] = mention_time
        body['app'] = task_info.get('app', '')
        body['cc_biz_id'] = task_info.get('cc_biz_id', '')
        body['operator'] = task_info.get('operator', '')
        body['operators'] = task_info.get('operators', '')
        body['title'] = task_info.get('title', '')
        body['operate_type'] = task_info.get('operate_type', '')
        response = requests.post(url, data=body)

        #mail_send
        body = {}
        body['name'] = "bk.tof.send_mail"
        body['kwargs'] = json.dumps({'sender': creator,
            'receiver': task_info.get('operators'),
            'title': message,
            'content': message})
        body['creator'] = creator
        body['crontab'] = ""
        body['time'] = mention_time
        body['app'] = task_info.get('app', '')
        body['cc_biz_id'] = task_info.get('cc_biz_id', '')
        body['operator'] = task_info.get('operator', '')
        body['operators'] = task_info.get('operators', '')
        body['title'] = task_info.get('title', '')
        body['operate_type'] = task_info.get('operate_type', '')
        response = requests.post(url, data=body)



#获取指定创建者的所有定时任务
def list_task_schedules(creator):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'creator': creator,
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_list_task_schedules'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


#根据schedule_id获取定时任务
def get_task_schedule(schedule_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'schedule_id': schedule_id
    }
    response = requests.post(url, args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_get_task_schedule'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


#根据schedule_id删除指定的定时任务, schedule_id由list_task_scheduls获取
def delete_task_schedule(schedule_id):
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'task-schedule',
        'schedule_id': schedule_id
    }
    response = requests.post(url, data=args)
    assert_http_call_is_successful(response)
    form_del_task_schedule = json.loads(response.content)['form_delete_task_schedule']
    http_call = getattr(requests, form_del_task_schedule['method'].lower())
    body = form_del_task_schedule['body']
    url = make_url_absolute(form_del_task_schedule['action'])
    response = http_call(url, data=body)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


#根据定时任务的schdule_id获取指定时间内生成的task
def get_tasks_by_schedule(schedule_id, datetime_created_ge, datetime_created_lt):
    """时间格式:"2014-08-25 00:00:00", 时间范围不能超时24小时"""
    import datetime
    deltahours = 24
    fmt="%Y-%m-%d %H:%M:%S"
    datetime_created_ge = datetime.datetime.strptime(datetime_created_ge, fmt)
    datetime_created_lt = datetime.datetime.strptime(datetime_created_lt, fmt)
    if datetime_created_lt - datetime_created_ge > datetime.timedelta(hours=deltahours):
        raise Exception('Too large time range.At most 24 hours.')
    url = make_url_absolute('/v1/search/')
    args = {
        'searching_type': 'tasks-by-schedule',
        'schedule_id': schedule_id,
        'datetime_created_ge': time.mktime(datetime_created_ge.timetuple()),
        'datetime_created_lt': time.mktime(datetime_created_lt.timetuple()),
    }
    response = requests.post(url, args)
    assert_http_call_is_successful(response)
    url = make_url_absolute(json.loads(response.content)['rel_get_tasks_by_schedule'])
    response = requests.get(url)
    assert_http_call_is_successful(response)
    return json.loads(response.content)


# 内部方法：对芯雲接口服务url的封装
def make_url_absolute(url, base_url=None):
    base_url = base_url or BPM_SERVICE_URL
    scheme, auth, host, port, path, query, fragment = requests.packages.urllib3.util.parse_url(url)
    if not scheme:
        return '%s%s' % (base_url, url)
    else:
        return url

def assert_http_call_is_successful(response):
    if httplib.OK != response.status_code:
        raise Exception('response status code: %s, %s' % (response.status_code, response.content))


def main():
    global BPM_SERVICE_URL
    import argparse
    import sys

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('--bpm-url', help='which bpm env to use', default='http://127.0.0.1:8001')
    parser.add_argument('command', help='change_task_step_args:123,some_step,{"arg1":"world"}')
    args = parser.parse_args()
    BPM_SERVICE_URL = args.bpm_url + '/service'
    LOGGER.info('BPM SERVICE URL: %s' % BPM_SERVICE_URL)
    raw_input('are you sure?')
    command_name, _, command_args = args.command.partition(':')
    command_func = getattr(sys.modules['__main__'], command_name)
    command_args = command_args.split(',')
    command_args = [json.loads(a) if a.startswith('{') and a.endswith('}') else a for a in command_args]
    result = command_func(*command_args)
    LOGGER.info('result: %s' % result)

if '__main__' == __name__:
    main()
