from helper_class import Task, TaskManager,TaskStatus
import unittest

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.shared_task = {
            "task1": Task(status=TaskStatus.QUEUED),
            "task2": Task(status=TaskStatus.RUNNING)
        }
        self.manager = TaskManager(shared_tasks=self.shared_task.copy())
        
    def test_add_task_default_status(self):
        """ Test adding a task without status, the default should be used here """
        self.manager.add_task("task3")
        task = self.manager.get_task("task3")
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatus.QUEUED)
                
    def test_get_task_existing(self):
        """Test retrieving an existing task."""
        task = self.manager.get_task("task1")
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatus.QUEUED)
        
    def test_add_task_custom_status(self):
        """Test adding a task with custom status."""
        self.manager.add_task("task4", status=TaskStatus.COMPLETED)
        task = self.manager.get_task("task4")
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        
    def test_add_invalid_task(self):
        f = self.manager.add_task
        with self.assertRaises(ValueError) as ar:
            f(task_id="task4", status="1234")
            
    def test_remove_class_default(self):
        """ removing a nonexistent task """
        result = self.manager.remove_task("task4")
        self.assertIsNone(result)
        
    def test_get_task_nonexistent(self):
        """Test retrieving a non-existent task."""
        task = self.manager.get_task("task999")
        self.assertIsNone(task)
        
    def test_update_task_nonexistent(self):
        """ updating a nonexistent task """
        result = self.manager.update_task(task_id="task4", status=TaskStatus.CANCELLED)
        self.assertFalse(result)
        
    def test_update_task_normal(self):
        """ test updating a task and checking the value of it """
        result = self.manager.update_task(task_id="task2", status=TaskStatus.CANCELLED)
        task = self.manager.get_task("task2")
        self.assertTrue(result)
        self.assertEqual(task.status,TaskStatus.CANCELLED)
        
    def test_remove_task_existent(self):
        """ remove a existing task """
        task = self.manager.remove_task("task1")
        original = self.manager.get_task("task1")
        self.assertEqual(task.status, TaskStatus.QUEUED)
        self.assertIsNone(original)

        

if __name__ == "__main__":
    unittest.main()