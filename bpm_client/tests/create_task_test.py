from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class CreateTaskTest(TestCase):
    def setUp(self):
        super(CreateTaskTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test_without_context(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

def empty_component():
    pass
        """)
        self.assertEqual([], list_tasks('bpmtest.empty_component'))
        create_task('bpmtest.empty_component').start()
        self.assertEqual(1, len(list_tasks('bpmtest.empty_component')))

    def test_with_context(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

def empty_component():
    pass
        """)
        self.assertEqual([], list_tasks('bpmtest.empty_component'))
        task = create_task('bpmtest.empty_component').hello('world').start()
        self.assertEqual({'hello': 'world'}, get_task(task['id'])['context'])
