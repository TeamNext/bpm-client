from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class RetryTaskTest(TestCase):
    def setUp(self):
        super(RetryTaskTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def some_task(input=''):
    if 'secret' != input:
        raise bpm_complete_task(return_code=1)
        """)
        task = start_task('bpmtest.some_task')
        task = self.execute_delayed_jobs(task['id'])
        self.assertEqual('FAILURE', get_task(task.id)['state'])
        task = retry_task(task.id, 'secret')
        task = self.execute_delayed_jobs(task['id'])
        self.assertEqual('SUCCESS', get_task(task.id)['state'])
