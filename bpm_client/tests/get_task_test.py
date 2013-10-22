from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class GetTaskTest(TestCase):
    def setUp(self):
        super(GetTaskTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def some_task():
    pass
        """)
        task = start_task('bpmtest.some_task')
        self.assertEqual('bpmtest.some_task', get_task(task['id'])['task_definition_name'])