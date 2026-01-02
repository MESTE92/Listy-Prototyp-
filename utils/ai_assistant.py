"""
AI Assistant Module
===================

Handles interactions with various AI providers (Gemini, OpenRouter, OpenAI).
Provides a unified interface for the chat system to send messages and receive responses,
including tool calling capabilities for list management.
"""
import google.generativeai as genai
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
import flet as ft
import json

# --- CONFIG ---
DEFAULT_OPENROUTER_KEY = "" # REPLACE THIS WITH YOUR KEY

class AIAssistant:
    def __init__(self, data_manager, api_key=None):
        self.data_manager = data_manager
        self.api_key = api_key
        # Load provider from settings, default to gemini
        self.provider = self.data_manager.get_settings().get("ai_provider", "gemini")
        self.gemini_model = None
        self.openai_client = None
        self.chat_session = None
        self.history = [] # For OpenAI/OpenRouter

        if self.api_key or self.provider == "openrouter":
            self.configure_model()

    def _resolve_model(self):
        """Finds the best available model for the user's API key (Gemini only)."""
        try:
            valid_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    valid_models.append(m.name)
            
            if not valid_models:
                return 'gemini-1.5-flash-latest' # Fallback
            
            # Priority List (Stability over Speed)
            # We prioritize explicit 1.5 Flash versions because 2.0-exp often has strict rate limits.
            priorities = [
                 "gemini-1.5-flash-002",
                 "gemini-1.5-flash-001",
                 "gemini-1.5-flash", 
                 "gemini-1.5-pro",
                 "gemini-pro"
            ]
            
            for p in priorities:
                for m in valid_models:
                     if m.endswith(p) or m == f"models/{p}":
                         return m
                         
            # If no specific match, fallback to any flash
            for m in valid_models:
                if "flash" in m and "exp" not in m:
                    return m

            return valid_models[0] # Fallback to first available
        except Exception as e:
            print(f"Error listing models: {e}")
            return 'gemini-1.5-flash-latest' # Hard fallback

    def configure_model(self):
        # OpenRouter Fallback Logic
        if self.provider == "openrouter":
            # Sanitize User Key (handle empty strings or spaces)
            user_key = str(self.api_key).strip() if self.api_key else ""
            key_to_use = user_key if user_key else DEFAULT_OPENROUTER_KEY.strip()
            
            if not key_to_use or key_to_use.startswith("sk-or-v1-..."):
                print(f"OpenRouter Key Invalid/Missing. (User Key length: {len(user_key)}, Default: {DEFAULT_OPENROUTER_KEY[:10]}...)")
                return # Can't configure without at least one key
                
            if OpenAI is None:
                print("OpenAI library not installed.")
                return

            print(f"Configuring OpenRouter (DeepSeek) with Key: {key_to_use[:10]}...{key_to_use[-4:]}")
            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key_to_use,
                default_headers={
                    "HTTP-Referer": "https://github.com/Starttoaster/Flet-To-Do-Liste", 
                    "X-Title": "Listy App",
                }
            )
            # OpenRouter typically doesn't use system messages in the history list for context management 
            # the same way pure OpenAI implementation might expect if we kept history manually,
            # but we use the same structure for simplicity.
            self.history = [{"role": "system", "content": self._get_system_prompt()}]
            return

        if not self.api_key:
            return

        if self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            model_name = self._resolve_model()
            print(f"Configuring Gemini with model: {model_name}")
            
            tools = [self._add_item_tool, self._remove_item_tool, self._create_list_tool, self._clear_list_tool, self._get_list_content_tool]
            self.gemini_model = genai.GenerativeModel(model_name=model_name, tools=tools)
            self._init_gemini_chat()

        elif self.provider == "openai":
            if OpenAI is None:
                print("OpenAI library not installed.")
                return
            self.openai_client = OpenAI(api_key=self.api_key)
            self.history = [{"role": "system", "content": self._get_system_prompt()}]
            print("Configuring OpenAI client...")

    def _get_system_prompt(self):
        return """You are a helpful AI Assistant for a Todo and Shopping List app named 'Listy'. 
        You have direct access to the user's lists via tools.
        
        Your capabilities:
        1. Add items to lists (Shopping or Todo).
        2. Remove items.
        3. Create new lists.
        4. Clear lists.
        5. Read list content to give context (e.g. suggesting recipes based on what's there).

        Rules:
        - You will receive the USER'S CURRENT CONTEXT (Mode and Active List) at the start of their message.
        - ALWAYS USE THIS CONTEXT to determine where to add/remove items. 
        - DO NOT ask "Which list?" or "Shopping or Todo?" if you have the context. Just do it.
        - Only ask if the user's request explicitly conflicts with the context (e.g. user says "add to todo" while in shopping mode).
        - When adding items for a recipe, list the ingredients you are adding.
        - Be concise and friendly.
        - Keep answers short.
        - German Language is preferred if the user speaks German.
        """

    def _init_gemini_chat(self):
        self.chat_session = self.gemini_model.start_chat(
            enable_automatic_function_calling=True,
            history=[
                {"role": "user", "parts": [self._get_system_prompt()]},
                {"role": "model", "parts": ["Understood. I am Listy AI. How can I help you today?"]}
            ]
        )

    def set_api_key(self, api_key, provider="gemini"):
        self.api_key = api_key
        self.provider = provider
        self.configure_model()

    def verify_api_key(self):
        """Attempts to verify the key and auto-find a working model."""
        if self.provider == "openrouter":
            # For OpenRouter we check logic slightly differently
            key = self.api_key if self.api_key else DEFAULT_OPENROUTER_KEY
            if not key or key == "sk-or-v1-...":
                return False, "No Key (Standard or Custom) set."
            try:
                # Simple list models check
                self.openai_client.models.list()
                return True, "OpenRouter Connected! ✅"
            except Exception as e:
                return False, f"OpenRouter Error: {str(e)}"

        if not self.api_key:
            return False, "No API Key set."
        
        if self.provider == "gemini":
            try:
                self.gemini_model.generate_content("Hi")
                return True, "Gemini Connected! ✅"
            except Exception as e:
                print(f"Default model failed: {e}")
                return self.configure_model() or (True, "Fixed connection via auto-discovery.")
        
        elif self.provider == "openai":
            try:
                self.openai_client.models.list()
                return True, "OpenAI Connected! ✅"
            except Exception as e:
                return False, f"OpenAI Error: {str(e)}"
        
        return False, "Unknown provider"

    def send_message(self, message, context=""):
        # For OpenRouter, key check is looser (can be default)
        if self.provider != "openrouter" and not self.api_key:
             return "Please configure your API Key in Settings first."
        if self.provider == "openrouter" and (not self.api_key and DEFAULT_OPENROUTER_KEY == "sk-or-v1-..."):
             return "Please configure a Key or set the Standard Key in code."
        
        full_message = f"{context}\n\n{message}" if context else message

        if self.provider == "gemini":
            return self._send_message_gemini(full_message)
        elif self.provider == "openai":
            return self._send_message_openai(full_message)
        elif self.provider == "openrouter":
            return self._send_message_openrouter(full_message)
        return "Unknown provider."

    def _send_message_gemini(self, message):
        try:
            if not self.chat_session:
                self._init_gemini_chat()
            response = self.chat_session.send_message(message)
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                return "⚠️ High Traffic (Quota Exceeded).\nPlease wait 1 minute and try again."
            return f"Error communicating with AI: {err_str}"

    def _send_message_openai(self, message):
        self.history.append({"role": "user", "content": message})
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_item",
                    "description": "Add an item to a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]},
                            "priority": {"type": "string", "enum": ["urgent", "medium", "low"]}
                        },
                        "required": ["item_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remove_item",
                    "description": "Remove an item from a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["item_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_list",
                    "description": "Create a new list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "list_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["list_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clear_list",
                    "description": "Clear all items from a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                             "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_list_content",
                    "description": "Get content of a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                             "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["mode"]
                    }
                }
            }
        ]

        try:
            # 1. First Call
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.history,
                tools=tools,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            self.history.append(response_message)

            tool_calls = response_message.tool_calls
            
            # 2. Check if function call needed
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    function_response = "Error"
                    if function_name == "add_item":
                        function_response = self._add_item_tool(**function_args)
                    elif function_name == "remove_item":
                        function_response = self._remove_item_tool(**function_args)
                    elif function_name == "create_list":
                        function_response = self._create_list_tool(**function_args)
                    elif function_name == "clear_list":
                        function_response = self._clear_list_tool(**function_args)
                    elif function_name == "get_list_content":
                        function_response = self._get_list_content_tool(**function_args)

                    # Append tool result
                    self.history.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                
                # 3. Second Call (Get final response)
                second_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.history,
                )
                final_text = second_response.choices[0].message.content
                self.history.append({"role": "assistant", "content": final_text})
                return final_text
            
            return response_message.content

        except Exception as e:
            return f"OpenAI Error: {str(e)}"

    def _send_message_openrouter(self, message):
        # OpenRouter (DeepSeek) logic
        # Very similar to OpenAI but forcing the model
        self.history.append({"role": "user", "content": message})
        
        # Tools definition (Same as OpenAI)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_item",
                    "description": "Add an item to a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]},
                            "priority": {"type": "string", "enum": ["urgent", "medium", "low"]}
                        },
                        "required": ["item_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remove_item",
                    "description": "Remove an item from a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["item_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_list",
                    "description": "Create a new list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "list_name": {"type": "string"},
                            "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["list_name", "mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clear_list",
                    "description": "Clear all items from a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                             "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_list_content",
                    "description": "Get content of a list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                             "mode": {"type": "string", "enum": ["shopping", "todo"]}
                        },
                        "required": ["mode"]
                    }
                }
            }
        ]

        try:
            # 1. First Call
            response = self.openai_client.chat.completions.create(
                model="deepseek/deepseek-chat", # FORCE DEEPSEEK
                messages=self.history,
                tools=tools,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            self.history.append(response_message)

            tool_calls = response_message.tool_calls
            
            # 2. Check if function call needed
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    function_response = "Error"
                    if function_name == "add_item":
                        function_response = self._add_item_tool(**function_args)
                    elif function_name == "remove_item":
                        function_response = self._remove_item_tool(**function_args)
                    elif function_name == "create_list":
                        function_response = self._create_list_tool(**function_args)
                    elif function_name == "clear_list":
                        function_response = self._clear_list_tool(**function_args)
                    elif function_name == "get_list_content":
                        function_response = self._get_list_content_tool(**function_args)

                    # Append tool result
                    self.history.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                
                # 3. Second Call (Get final response)
                second_response = self.openai_client.chat.completions.create(
                    model="deepseek/deepseek-chat",
                    messages=self.history,
                )
                final_text = second_response.choices[0].message.content
                self.history.append({"role": "assistant", "content": final_text})
                return final_text
            
            return response_message.content

        except Exception as e:
            return f"OpenRouter Error: {str(e)}"


    # --- Tool Definitions ---

    def _add_item_tool(self, item_name: str, mode: str, priority: str = "medium"):
        """Adds an item to the current list. 'mode' must be 'shopping' or 'todo' based on user context."""
        print(f"[AI Action] Adding {item_name} to {mode}...")
        self.data_manager.add_task(item_name, priority=priority, mode=mode)
        return f"Added '{item_name}' to {mode} list."

    def _remove_item_tool(self, item_name: str, mode: str):
        """Removes an item from the list. 'mode' must be 'shopping' or 'todo'."""
        print(f"[AI Action] Removing {item_name} from {mode}...")
        self.data_manager.delete_task(item_name, mode=mode)
        return f"Removed '{item_name}' from {mode} list."

    def _create_list_tool(self, list_name: str, mode: str):
        """Creates a new list. 'mode' is required."""
        if mode == "shopping":
            self.data_manager.create_shopping_list(list_name)
        else:
            self.data_manager.create_todo_list(list_name)
        return f"Created new {mode} list: '{list_name}'."

    def _clear_list_tool(self, mode: str):
        """Clears all items from the list. 'mode' is required."""
        self.data_manager.clear_tasks(mode=mode)
        return f"Cleared all items from {mode} list."

    def _get_list_content_tool(self, mode: str):
        """Gets content of the list. 'mode' is required."""
        items = self.data_manager.get_tasks(mode=mode)
        names = [item["name"] for item in items]
        return json.dumps(names)
