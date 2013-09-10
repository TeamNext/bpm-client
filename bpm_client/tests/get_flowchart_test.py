from django.test import TestCase

from bpm.kernel.tests.helper import *
from bpm_client.client import *
from .client_test_helper import run_test_server


class GetFlowchartTest(TestCase):
    def setUp(self):
        super(GetFlowchartTest, self).setUp()
        apply_context(self, run_test_server())
        self.repo = InMemoryRepository()
        apply_context(self, mock_bpm_kernel(self.repo))

    def test_one_step(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

class EmptyComponent(AbstractComponent):
    def start(self, arg1=None):
        self.complete()
class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(EmptyComponent).execute()
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
        self.assertEqual(1, len(flowchart))
        stage1 = flowchart[0]
        self.assertEqual(1, len(stage1))
        step1 = stage1[0]
        self.assertEqual('EmptyComponent', step1['description'])

    def test_serial(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

class EmptyComponent(AbstractComponent):
    def start(self, arg1=None):
        self.complete()
class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(EmptyComponent).execute()
        step2 = self.step(EmptyComponent).after(step1).execute() # after syntax
        step3 = step2.step(EmptyComponent).after(step2).execute() # chained syntax
        step4 = self.step(EmptyComponent).execute(step3) # argument dependency
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
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

class EmptyComponent(AbstractComponent):
    def start(self, arg1=None):
        self.complete()
class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(EmptyComponent).execute()
        step2 = self.step(EmptyComponent).execute()
        step3 = self.step(EmptyComponent).execute()
        step4 = self.step(EmptyComponent).execute()
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
        self.assertEqual(1, len(flowchart))
        stage1 = flowchart[0]
        self.assertEqual(4, len(stage1))


    def test_join(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

class EmptyComponent(AbstractComponent):
    def start(self, arg1=None):
        self.complete()
class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(EmptyComponent).execute()
        step2 = self.step(EmptyComponent).execute()
        step3 = self.step(EmptyComponent).after(step1, step2).execute()
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
        self.assertEqual(2, len(flowchart))
        stage1 = flowchart[0]
        stage2 = flowchart[1]
        self.assertEqual(2, len(stage1))
        self.assertEqual(1, len(stage2))

    def test_sort(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

class EmptyComponent(AbstractComponent):
    def start(self, arg1=None):
        self.complete()
class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(EmptyComponent).execute()
        step21 = self.step(EmptyComponent).after(step1).execute()
        step22 = self.step(EmptyComponent).after(step1).execute()
        step32 = self.step(EmptyComponent).after(step1, step22).execute()
        step31 = self.step(EmptyComponent).after(step21).execute()
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
        self.assertEqual(3, len(flowchart))
        stage1 = flowchart[0]
        stage2 = flowchart[1]
        stage3 = flowchart[2]
        self.assertEqual(1, len(stage1))
        self.assertEqual(2, len(stage2))
        self.assertEqual(2, len(stage3))
        self.assertEqual(1, len(stage3[0]['predecessors']))
        self.assertEqual(2, len(stage3[1]['predecessors']))

    def test_function(self):
        self.repo.set_data('bpmtest|tip|bpmtest/__init__.py', """
from bpm.kernel import *

class SerialProcess(AbstractProcess):
    def steps(self):
        step1 = self.step(self.do_x).execute()
        step2 = self.step(self.do_y).execute()
    def do_x(self):
        pass
    def do_y(self):
        pass
        """)
        flowchart = get_default_flowchart('bpmtest.SerialProcess')
        self.assertEqual(1, len(flowchart))
        stage1 = flowchart[0]
        self.assertEqual(2, len(stage1))
