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

    def test_one_step(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def serial_process():
    @step('Some Step')
    def some_step():
        pass
        """)
        flowchart = get_task_definition_flowchart('bpmtest.serial_process')
        self.assertEqual(1, len(flowchart))
        stage1 = flowchart[0]
        self.assertEqual(1, len(stage1))
        step1 = stage1[0]
        self.assertEqual('Some Step', step1['description'])

    def test_serial(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def serial_process():
    @step
    def step1():
        pass
    @step(after=step1)
    def step2():
        pass
    @step(after=step2)
    def step3():
        pass
    @step(after=step3)
    def step4():
        pass
        """)
        flowchart = get_task_definition_flowchart('bpmtest.serial_process')
        self.assertEqual(4, len(flowchart))
        stage1 = flowchart[0]
        stage2 = flowchart[1]
        stage3 = flowchart[2]
        stage4 = flowchart[3]
        self.assertEqual(1, len(stage1))
        self.assertEqual(1, len(stage2))
        self.assertEqual(1, len(stage3))
        self.assertEqual(1, len(stage4))
        self.assertEqual([], stage1[0]['predecessors'])
        self.assertEqual([stage1[0]['name']], stage2[0]['predecessors'])
        self.assertEqual([stage2[0]['name']], stage3[0]['predecessors'])
        self.assertEqual([stage3[0]['name']], stage4[0]['predecessors'])

    def test_parallel(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def serial_process():
    @step
    def step1():
        pass
    @step
    def step2():
        pass
    @step
    def step3():
        pass
    @step
    def step4():
        pass
        """)
        flowchart = get_task_definition_flowchart('bpmtest.serial_process')
        self.assertEqual(1, len(flowchart))
        stage1 = flowchart[0]
        self.assertEqual(4, len(stage1))


    def test_join(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def serial_process():
    @step
    def step1():
        pass
    @step
    def step2():
        pass
    @step
    def step3():
        return step1() + step2()
        """)
        flowchart = get_task_definition_flowchart('bpmtest.serial_process')
        self.assertEqual(2, len(flowchart))
        stage1 = flowchart[0]
        stage2 = flowchart[1]
        self.assertEqual(2, len(stage1))
        self.assertEqual(1, len(stage2))

    def test_sort(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

@task
def serial_process():
    @step
    def step1():
        pass
    @step(after=step1)
    def step21():
        pass
    @step(after=step1)
    def step22():
        pass
    @step(after=[step1,step22])
    def step32():
        pass
    @step(after=[step21])
    def step31():
        pass
        """)
        flowchart = get_task_definition_flowchart('bpmtest.serial_process')
        self.assertEqual(3, len(flowchart))
        stage1 = flowchart[0]
        stage2 = flowchart[1]
        stage3 = flowchart[2]
        self.assertEqual(1, len(stage1))
        self.assertEqual(2, len(stage2))
        self.assertEqual(2, len(stage3))
        self.assertEqual(1, len(stage3[0]['predecessors']))
        self.assertEqual(2, len(stage3[1]['predecessors']))
