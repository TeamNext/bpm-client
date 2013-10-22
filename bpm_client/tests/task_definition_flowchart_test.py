from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class GetTaskDefinitionFlowchartTest(TestCase):
    def setUp(self):
        super(GetTaskDefinitionFlowchartTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test_no_argument(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def some_task():
    @step
    def step1():
        pass
        """)
        self.assertEqual(1, len(get_task_definition_flowchart('bpmtest.some_task')))

    def test_with_argument(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def some_task(count):
    for i in range(count):
        @step
        def step1():
            pass
        """)
        self.assertEqual(2, len(get_task_definition_flowchart('bpmtest.some_task', 2)))
