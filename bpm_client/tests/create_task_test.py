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

    def test(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import AbstractComponent
from bpm.logging import get_logger

logger = get_logger()

class EmptyComponent(AbstractComponent):
    def start(self):
        logger.debug('Component start')
        self.complete()
        """)
        self.assertEqual([], list_tasks('bpmtest.EmptyComponent'))
        create_task('bpmtest.EmptyComponent')
        self.assertEqual(1, len(list_tasks('bpmtest.EmptyComponent')))
