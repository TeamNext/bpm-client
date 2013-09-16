from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server
from bpm.kernel import states

class SuspendTaskTest(TestCase):
    def setUp(self):
        super(SuspendTaskTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def loop_forever():
    while True:
        bpm_sleep(5)
        """)
        self.assertEqual([], list_tasks('bpmtest.loop_forever'))
        task_res = start_task('bpmtest.loop_forever')
        task = self.execute_delayed_jobs(task_res['id'])
        self.assertEqual(states.BLOCKED, task.state)

        suspend_task(task.id)
        task = self.execute_delayed_jobs(task.id)
        self.assertEqual(states.SUSPENDED, task.state)

        resume_task(task.id)
        task = self.execute_delayed_jobs(task.id)
        self.assertEqual(states.BLOCKED, task.state)
