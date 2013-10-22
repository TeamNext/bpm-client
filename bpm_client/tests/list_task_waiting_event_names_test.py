from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class ListTaskWaitingEventNamesTest(TestCase):
    def setUp(self):
        super(ListTaskWaitingEventNamesTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def some_task():
    bpm_wait_callback('hello')
        """)
        task = start_task('bpmtest.some_task')
        task = self.execute_delayed_jobs(task['id'])
        self.assertEqual(['hello'], list_task_waiting_event_names(task.id))