
import unittest
import json
import os
import shutil
import flet as ft
from unittest.mock import MagicMock
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.data_manager import DataManager, DEFAULT_TODO_DATA, DEFAULT_SHOPPING_DATA

class TestDataManager(unittest.TestCase):
    def setUp(self):
        # Mock Page and ClientStorage
        self.mock_page = MagicMock()
        self.mock_storage = {}
        
        # Define behavior for client_storage.get/set
        self.mock_page.client_storage.get.side_effect = lambda k: self.mock_storage.get(k)
        self.mock_page.client_storage.set.side_effect = lambda k, v: self.mock_storage.update({k: v})
        
        # Initialize DataManager with mock page
        self.dm = DataManager(self.mock_page)
        
        # Reset data to defaults for testing
        self.dm.todo_data = json.loads(json.dumps(DEFAULT_TODO_DATA))
        self.dm.shopping_data = json.loads(json.dumps(DEFAULT_SHOPPING_DATA))

    def test_add_todo_task(self):
        task = self.dm.add_task("Buy Milk", priority="urgent", mode="todo")
        self.assertIsNotNone(task)
        self.assertEqual(task["name"], "Buy Milk")
        self.assertEqual(task["priority"], "urgent")
        
        # Verify it's in the list
        current_id = self.dm.get_current_todo_list_id()
        items = self.dm.todo_data["lists"][current_id]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Buy Milk")

    def test_add_shopping_task(self):
        task = self.dm.add_task("Apples", is_completed=False, mode="shopping")
        self.assertIsNotNone(task)
        
        # Verify in shopping list
        current_id = self.dm.get_current_shopping_list_id()
        items = self.dm.shopping_data["lists"][current_id]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Apples")

    def test_complete_task(self):
        self.dm.add_task("Run Test", mode="todo")
        self.dm.update_task_status("Run Test", True, mode="todo")
        
        current_id = self.dm.get_current_todo_list_id()
        items = self.dm.todo_data["lists"][current_id]["items"]
        self.assertTrue(items[0]["is_completed"])

    def test_clear_completed_tasks_todo(self):
        # Add 3 tasks: 2 done, 1 active
        self.dm.add_task("Task 1", is_completed=True, mode="todo")
        self.dm.add_task("Task 2", is_completed=False, mode="todo")
        self.dm.add_task("Task 3", is_completed=True, mode="todo")
        
        current_id = self.dm.get_current_todo_list_id()
        before_count = len(self.dm.todo_data["lists"][current_id]["items"])
        self.assertEqual(before_count, 3)
        
        self.dm.clear_completed_tasks(mode="todo")
        
        after_items = self.dm.todo_data["lists"][current_id]["items"]
        self.assertEqual(len(after_items), 1)
        self.assertEqual(after_items[0]["name"], "Task 2")

    def test_duplicate_prevention_shopping(self):
        self.dm.add_task("Banana", mode="shopping")
        result = self.dm.add_task("banana", mode="shopping") # Should fail (case-insensitive)
        
        self.assertIsNone(result)
        current_id = self.dm.get_current_shopping_list_id()
        items = self.dm.shopping_data["lists"][current_id]["items"]
        self.assertEqual(len(items), 1)

if __name__ == '__main__':
    unittest.main()
