import unittest
import dataclasses

from helper_class import Task,TaskStatus

class TestTask(unittest.TestCase):
    def setUp(self):
        self.task = Task(status=TaskStatus.QUEUED)
        
    def test_status(self):
        status = self.task.status
        self.assertEqual(status, TaskStatus.QUEUED)
        
    def test_invalid_status(self):
        with self.assertRaises(ValueError) as ar:
            task = Task(status="1234")
    
    def test_frozen_task(self):
        with self.assertRaises(dataclasses.FrozenInstanceError) as ar:
            self.task.status = "1234"
            
            
if __name__ == "__main__":
    unittest.main()