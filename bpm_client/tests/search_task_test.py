from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm.kernel.models import Task
from bpm_client.client import *
from .client_test_helper import run_test_server
from datetime import datetime

class SearchTaskTest(TestCase):
    def setUp(self):
        super(SearchTaskTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import AbstractComponent
from bpm.logging import get_logger

logger = get_logger()

class EmptyComponent(AbstractComponent):
    def start(self):
        logger.debug('Component start')
        self.complete()
        """)

    def test_search_by_date_created(self):
        task = Task.objects.get(pk=create_task('bpmtest.EmptyComponent')['id'])
        task.date_created = datetime(2008, 8, 8)
        task.save()
        tasks = list_tasks(
            'bpmtest.EmptyComponent',
            date_created_ge=datetime(2008, 8, 8),
            date_created_lt=datetime(2008, 8, 9))
        self.assertEqual(1, len(tasks))
        task = Task.objects.get(pk=create_task('bpmtest.EmptyComponent')['id'])
        task.date_created = datetime(2008, 8, 9)
        task.save()
        tasks = list_tasks(
            'bpmtest.EmptyComponent',
            date_created_ge=datetime(2008, 8, 8),
            date_created_lt=datetime(2008, 8, 9))
        self.assertEqual(1, len(tasks))
        tasks = list_tasks(
            'bpmtest.EmptyComponent',
            date_created_ge=datetime(2008, 8, 8),
            date_created_lt=datetime(2008, 8, 10))
        self.assertEqual(2, len(tasks))

    def test_search_by_context(self):
        task = create_task('bpmtest.EmptyComponent')
        self.assertEqual(1, len(list_tasks('bpmtest.EmptyComponent')))
        self.assertEqual(0, len(list_tasks('bpmtest.EmptyComponent', context_eq={
            'operator': 'wentao'
        })))
        set_task_context(task['id'], 'operator', 'wentao')
        self.assertEqual(1, len(list_tasks('bpmtest.EmptyComponent', context_eq={
            'operator': 'wentao'
        })))