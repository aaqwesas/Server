import time
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import create_app
from configs import  PORT,WS_URL, BASE_URL
from helper_class import TaskStatus


class TestTasksRoute(unittest.TestCase):
    def setUp(self):
        """Method to prepare the test fixture. Run BEFORE the test methods."""
        self.base_url: str = f"{BASE_URL}:{PORT}/tasks"
        self.app: FastAPI = create_app()
        self.client = TestClient(app=self.app)
        self.task_id = "20250405123045123456" 
        
    def tearDown(self):
        """Method to tear down the test fixture. Run AFTER the test methods."""
        pass
    
    def test_get_id_route(self):
        response = self.client.get(f"{self.base_url}/getid")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data,dict)
        self.assertGreaterEqual(len(data["task_id"]),20)
        
    def test_start_route(self):
        with self.client as c:
            response = c.post(url=f"{self.base_url}/start/{self.task_id}")
            data = response.json()
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(data,dict)
            self.assertEqual(data["task_id"],self.task_id)
            self.assertEqual(data["status"],TaskStatus.QUEUED)
            
    def test_list_task_route(self):
        with self.client as c:
            response = c.get(url=f"{self.base_url}/list/")
            data = response.json()
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(data,dict)
            self.assertEqual(data, {})
            c.post(url=f"{self.base_url}/start/{self.task_id}")
            response = c.get(url=f"{self.base_url}/list/")
            data = response.json()
            self.assertEqual(response.status_code,200)
            self.assertIsInstance(data,dict)
            self.assertIn(self.task_id,data)
            self.assertEqual(data[self.task_id]["status"],TaskStatus.QUEUED)
            
            
    def test_stop_task_route(self):
        with self.client as c:
            test_dict = {"task_id": self.task_id, "status": TaskStatus.CANCELLED}
            response = c.post(url=f"{self.base_url}/stop/{self.task_id}")
            self.assertEqual(response.status_code,404)
            c.post(url=f"{self.base_url}/start/{self.task_id}")
            response = c.post(url=f"{self.base_url}/stop/{self.task_id}")
            data = response.json()
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(data, test_dict)
            
               
    def test_health_route(self):
        with self.client as c:
            response = c.get(url=f"{self.base_url}/health")
            data = response.json()
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(data,dict)
               
    
            
            

    
        

if __name__ == "__main__":
    unittest.main()

