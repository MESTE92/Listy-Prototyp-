"""
Data Manager Module
===================

Handles data persistence and state management for Listy.
Uses Flet's ClientStorage to save data locally in the user's browser/app data.

Manages:
- Todo Lists
- Shopping Lists
- Application Settings
- User Suggestions (learned items)
"""
import json
import os
import uuid
import flet as ft
from utils.suggestions import SUGGESTIONS

TODO_FILE = "storage/todo.json"
SHOPPING_FILE = "storage/shopping.json"

DEFAULT_TODO_DATA = {
    "settings": {
        "language": "en",
        "mode": "todo",
        "theme_mode": "dark"
    },
    "current_list_id": "default",
    "lists": {
        "default": {
            "name": "Allgemein",
            "items": []
        }
    }
}

DEFAULT_SHOPPING_DATA = {
    "current_list_id": "default",
    "lists": {
        "default": {
            "name": "Einkaufsliste",
            "items": []
        }
    }
}

class DataManager:
    """
    Central class for managing application state and persistence.
    Wraps Flet's client_storage to provide a clean API for reading/writing tasks and settings.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        # Keys for ClientStorage
        self.TODO_KEY = "listy.todo_data"
        self.SHOPPING_KEY = "listy.shopping_data"
        
        # Load Data from ClientStorage
        self.todo_data = self.page.client_storage.get(self.TODO_KEY)
        self.shopping_data = self.page.client_storage.get(self.SHOPPING_KEY)
        self.user_suggestions_data = self.page.client_storage.get("listy.user_suggestions")
        if self.user_suggestions_data is None:
            self.user_suggestions_data = []
            self.page.client_storage.set("listy.user_suggestions", [])
        
        # Migration from File System (One-time check if ClientStorage is empty but files exist)
        if self.todo_data is None and os.path.exists(TODO_FILE):
             print("Migrating Todo Data from File to ClientStorage...")
             self.todo_data = self.load_json_file(TODO_FILE, DEFAULT_TODO_DATA)
             self.save_todo() # Save to ClientStorage
             
        if self.shopping_data is None and os.path.exists(SHOPPING_FILE):
             print("Migrating Shopping Data from File to ClientStorage...")
             self.shopping_data = self.load_json_file(SHOPPING_FILE, DEFAULT_SHOPPING_DATA)
             self.save_shopping() # Save to ClientStorage

        # Initialize Defaults if still None
        if self.todo_data is None:
            self.todo_data = DEFAULT_TODO_DATA
            self.save_todo()
            
        if self.shopping_data is None:
            self.shopping_data = DEFAULT_SHOPPING_DATA
            self.save_shopping()

        # --- Data Integrity Checks / Migrations (Same logic as before) ---
        
        # Migration Check for Shopping Data
        if "lists" not in self.shopping_data:
            print("Migrating Shopping Data Structure...")
            old_tasks = self.shopping_data.get("tasks", [])
            self.shopping_data["current_list_id"] = "default"
            self.shopping_data["lists"] = {
                "default": {
                    "name": "Allgemein",
                    "items": old_tasks
                }
            }
            if "tasks" in self.shopping_data:
                del self.shopping_data["tasks"]
            self.save_shopping()
            
        # Migration Check for Todo Data (New)
        if "lists" not in self.todo_data:
            print("Migrating Todo Data Structure...")
            old_tasks = self.todo_data.get("tasks", [])
            self.todo_data["current_list_id"] = "default"
            self.todo_data["lists"] = {
                "default": {
                    "name": "Allgemein",
                    "items": old_tasks
                }
            }
            if "tasks" in self.todo_data:
                del self.todo_data["tasks"]
            self.save_todo()
        
        # Ensure default list name is "Allgemein" for both todo and shopping
        if "lists" in self.shopping_data and "default" in self.shopping_data["lists"]:
             if self.shopping_data["lists"]["default"]["name"] in ["Einkaufsliste", "Shopping List", "购物清单", "買い物リスト"]:
                 self.shopping_data["lists"]["default"]["name"] = "Allgemein"
                 self.save_shopping()
        
        if "lists" in self.todo_data and "default" in self.todo_data["lists"]:
             if self.todo_data["lists"]["default"]["name"] != "Allgemein": # Force standard name for protection consistency
                 self.todo_data["lists"]["default"]["name"] = "Allgemein"
                 self.save_todo()

    # Helper for one-time migration
    def load_json_file(self, filepath, default):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def save_todo(self):
        self.page.client_storage.set(self.TODO_KEY, self.todo_data)
    
    def save_shopping(self):
        self.page.client_storage.set(self.SHOPPING_KEY, self.shopping_data)

    def save_user_suggestions(self):
        self.page.client_storage.set("listy.user_suggestions", self.user_suggestions_data)

    def learn_suggestion(self, item_name):
        # Don't learn empty or short suggestions (optional check, but good for safety)
        if not item_name or len(item_name) < 2:
            return

        # Check if exists in static suggestions (case-insensitive)
        for s in SUGGESTIONS:
            if s.lower() == item_name.lower():
                return # Already known

        # Check if exists in user data (case-insensitive)
        for s in self.user_suggestions_data:
            if s.lower() == item_name.lower():
                return # Already known

        # Learn new item
        self.user_suggestions_data.append(item_name)
        self.user_suggestions_data.sort() # Keep sorted
        self.save_user_suggestions()
        print(f"Learned new item: {item_name}")
    
    def get_all_suggestions(self):
        # Combine static and user suggestions
        # Using a set for duplicate removal just in case, though logic prevents it
        combined = set(SUGGESTIONS + self.user_suggestions_data)
        return sorted(list(combined))

    # --- Settings (Always in Todo Data) ---
    def get_settings(self):
        return self.todo_data.get("settings", DEFAULT_TODO_DATA["settings"])

    def update_setting(self, key, value):
        self.todo_data["settings"][key] = value
        self.save_todo()

    # --- Generic List Management (Helper) ---
    def _get_lists(self, mode):
        data = self.shopping_data if mode == "shopping" else self.todo_data
        lists = {}
        for l_id, l_data in data.get("lists", {}).items():
            lists[l_id] = l_data["name"]
        return lists

    def _create_list(self, name, mode):
        new_id = str(uuid.uuid4())[:8]
        data = self.shopping_data if mode == "shopping" else self.todo_data
        
        if "lists" not in data:
            data["lists"] = {}

        data["lists"][new_id] = {
            "name": name,
            "items": []
        }
        self._set_current_list_id(new_id, mode)
        
        if mode == "shopping":
            self.save_shopping()
        else:
            self.save_todo()
        return new_id

    def _get_current_list_id(self, mode):
        data = self.shopping_data if mode == "shopping" else self.todo_data
        return data.get("current_list_id", "default")
    
    def _set_current_list_id(self, list_id, mode):
        data = self.shopping_data if mode == "shopping" else self.todo_data
        if "lists" in data and list_id in data["lists"]:
            data["current_list_id"] = list_id
            if mode == "shopping":
                self.save_shopping()
            else:
                self.save_todo()

    def _rename_list(self, list_id, new_name, mode):
        data = self.shopping_data if mode == "shopping" else self.todo_data
        if "lists" in data and list_id in data["lists"]:
            data["lists"][list_id]["name"] = new_name
            if mode == "shopping":
                self.save_shopping()
            else:
                self.save_todo()

    def _delete_list(self, list_id, mode):
        # Prevent deleting the default 'Allgemein' list
        if list_id == "default":
            return False

        data = self.shopping_data if mode == "shopping" else self.todo_data

        # Prevent deleting the last list (backup check)
        if len(data.get("lists", {})) <= 1:
            return False
            
        if "lists" in data and list_id in data["lists"]:
            del data["lists"][list_id]
            
            # If we deleted the current list, switch to another one
            if data.get("current_list_id") == list_id:
                # Pick the first available key
                first_key = next(iter(data["lists"]))
                data["current_list_id"] = first_key
            
            if mode == "shopping":
                self.save_shopping()
            else:
                self.save_todo()
            return True
        return False

    # --- Public List Management API ---
    def get_shopping_lists(self): return self._get_lists("shopping")
    def create_shopping_list(self, name): return self._create_list(name, "shopping")
    def get_current_shopping_list_id(self): return self._get_current_list_id("shopping") # updated name
    def set_current_shopping_list_id(self, list_id): self._set_current_list_id(list_id, "shopping")
    def rename_shopping_list(self, list_id, new_name): self._rename_list(list_id, new_name, "shopping")
    def delete_shopping_list(self, list_id): return self._delete_list(list_id, "shopping")

    def get_todo_lists(self): return self._get_lists("todo")
    def create_todo_list(self, name): return self._create_list(name, "todo")
    def get_current_todo_list_id(self): return self._get_current_list_id("todo")
    def set_current_todo_list_id(self, list_id): self._set_current_list_id(list_id, "todo")
    def rename_todo_list(self, list_id, new_name): self._rename_list(list_id, new_name, "todo")
    def delete_todo_list(self, list_id): return self._delete_list(list_id, "todo")
    
    # Backwards compatibility alias for Shopping View 
    # (TodoView logic calls "get_current_list_id" without args for shopping in old code, but we'll refactor view)
    def get_current_list_id(self): return self.get_current_shopping_list_id()

    # --- Sharing ---
    def get_list_as_text(self, mode="todo"):
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            list_name = self.shopping_data["lists"][current_id]["name"]
            items = self.shopping_data["lists"][current_id]["items"]
        else:
            current_id = self.get_current_todo_list_id()
            list_name = self.todo_data["lists"][current_id]["name"]
            items = self.todo_data["lists"][current_id]["items"]
            
        text = f"📝 {list_name}\n\n"
        for item in items:
            status = "✅" if item["is_completed"] else "⬜"
            text += f"{status} {item['name']}\n"
            
        return text

    # --- Tasks ---
    def get_tasks(self, mode="todo"):
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            return self.shopping_data["lists"].get(current_id, {}).get("items", [])
        else:
            current_id = self.get_current_todo_list_id()
            return self.todo_data["lists"].get(current_id, {}).get("items", [])

    def add_task(self, task_name, priority="medium", is_completed=False, mode="todo"):
        clean_name = task_name.strip()
        if not clean_name:
            return None

        # 1. Normalization (Auto-Correction)
        # Check if matched in suggestions (case-insensitive) to use standard casing
        # This fixes "gemüse" -> "Gemüse"
        all_suggestions = self.get_all_suggestions()
        for suggestion in all_suggestions:
            if suggestion.lower() == clean_name.lower():
                clean_name = suggestion
                break
        
        # Learn the item if it's new (only for shopping mode usually, but harmless for todo)
        if mode == "shopping":
            self.learn_suggestion(clean_name)
        
        # 2. Duplicate Prevention
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            current_items = self.shopping_data["lists"][current_id]["items"]
        else:
            current_id = self.get_current_todo_list_id()
            current_items = self.todo_data["lists"][current_id]["items"]
            
        # Check if exists (case-insensitive)
        for item in current_items:
            if item["name"].lower() == clean_name.lower():
                return None # Duplicate found, do not add

        new_task = {
            "name": clean_name,
            "priority": priority, # urgent, medium, low
            "is_completed": is_completed
        }
        
        if mode == "shopping":
            self.shopping_data["lists"][current_id]["items"].append(new_task)
            self.save_shopping()
        else:
            self.todo_data["lists"][current_id]["items"].append(new_task)
            self.save_todo()
            
        return new_task

    def update_task_status(self, task_name, is_completed, mode="todo"):
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            tasks = self.shopping_data["lists"][current_id]["items"]
        else:
            current_id = self.get_current_todo_list_id()
            tasks = self.todo_data["lists"][current_id]["items"]
        
        for task in tasks:
            if task["name"] == task_name: 
                task["is_completed"] = is_completed
                break
        
        if mode == "shopping":
            self.save_shopping()
        else:
            self.save_todo()

    def delete_task(self, task_name, mode="todo"):
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            old_items = self.shopping_data["lists"][current_id]["items"]
            self.shopping_data["lists"][current_id]["items"] = [t for t in old_items if t["name"] != task_name]
            self.save_shopping()
        else:
            current_id = self.get_current_todo_list_id()
            old_items = self.todo_data["lists"][current_id]["items"]
            self.todo_data["lists"][current_id]["items"] = [t for t in old_items if t["name"] != task_name]
            self.save_todo()

    def clear_shopping_cart(self):
        """Removes only completed items from the current shopping list."""
        current_id = self.get_current_shopping_list_id()
        if current_id in self.shopping_data["lists"]:
            items = self.shopping_data["lists"][current_id]["items"]
            # Keep only items that are NOT completed
            self.shopping_data["lists"][current_id]["items"] = [t for t in items if not t["is_completed"]]
            self.save_shopping()

    def clear_tasks(self, mode="todo"):
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            self.shopping_data["lists"][current_id]["items"] = []
            self.save_shopping()
        else:
            current_id = self.get_current_todo_list_id()
            self.todo_data["lists"][current_id]["items"] = []
            self.save_todo()

    def clear_completed_tasks(self, mode="todo"):
        """Removes only completed items from the current list."""
        if mode == "shopping":
            current_id = self.get_current_shopping_list_id()
            data = self.shopping_data
        else:
            current_id = self.get_current_todo_list_id()
            data = self.todo_data
        
        if current_id in data["lists"]:
            items = data["lists"][current_id]["items"]
            # Keep only items that are NOT completed
            data["lists"][current_id]["items"] = [t for t in items if not t["is_completed"]]
            
            if mode == "shopping":
                self.save_shopping()
            else:
                self.save_todo()
