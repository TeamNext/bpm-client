from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server
from bpm.kernel import states
import requests

class WaitCallbackFromBkTest(TestCase):
    def setUp(self):
        super(WaitCallbackFromBkTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test_wait_from_main(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def call_bk_l2():
    bpm_wait_callback('bk_l2_callback:%s' % bpm_context.step_name)
        """)
        task = create_task('bpmtest.call_bk_l2')
        task = self.execute_delayed_jobs(task['id'])
        self.assertEqual(states.BLOCKED, task.state)
        requests.post('http://127.0.0.1:7999/v1/task/%s/main/transitions/to-ready/' % task.id)
        task = self.execute_delayed_jobs(task.id)
        self.assertEqual(states.SUCCESS, task.state)

    def test_wait_from_step(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def call_bk_l2():
    @step
    def some_step():
        bpm_wait_callback('bk_l2_callback:%s' % bpm_context.step_name)
        """)
        task = create_task('bpmtest.call_bk_l2')
        task = self.execute_delayed_jobs(task['id'])
        self.assertEqual(states.BLOCKED, task.state)
        requests.post('http://127.0.0.1:7999/v1/task/%s/some_step/transitions/to-ready/' % task.id)
        task = self.execute_delayed_jobs(task.id)
        self.assertEqual(states.SUCCESS, task.state)
