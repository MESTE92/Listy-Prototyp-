# Architecture Documentation

## Overview
Listy is a Flet-based Python application that combines Todo List and Shopping List functionality with AI assistance. It follows a modular architecture separating UI (Views), State Management (Data Manager), and External Services (AI/Voice).

## Component Diagram
```mermaid
graph TD
    User([User])
    
    subgraph UI Layer
        Main[main.py: App Entry]
        TodoView[views/todo_view.py: Task Management UI]
        Chat[Chat Dialog: AI Interface]
    end
    
    subgraph Logic Layer
        AI[utils/ai_assistant.py: AI Logic]
        Voice[utils/voice.py: Speech Recognition]
        I18n[utils/translations.py: Language Manager]
    end
    
    subgraph Data Layer
        DataManager[storage/data_manager.py: State Store]
        ClientStorage[(Flet ClientStorage)]
    end
    
    subgraph External Services
        Gemini[Google Gemini API]
        OpenRouter[OpenRouter / DeepSeek]
        OpenAI[OpenAI / OpenAI-Like]
    end

    User --> Main
    Main --> TodoView
    Main --> Chat
    Main --> I18n
    
    TodoView --> DataManager
    Chat --> AI
    Chat --> Voice
    
    AI --> DataManager : Read Context / Add Tasks
    AI --> Gemini
    AI --> OpenRouter
    AI --> OpenAI
    
    DataManager --> ClientStorage : Persist Data
```

## Directory Structure
- `main.py`: Entry point. Sets up the Flet page, Theme, and Footer. Orchestrates Views.
- `views/`: Contains UI components.
  - `todo_view.py`: Main view logic for displaying and managing lists.
- `components/`: Reusable UI widgets.
  - `task_item.py`: Individual task row with checkbox and delete button.
- `utils/`: Helper modules.
  - `ai_assistant.py`: unified interface for AI providers.
  - `voice.py`: Wrapper for speech recognition.
  - `translations.py`: Dictionary-based localization.
- `storage/`: Data persistence.
  - `data_manager.py`: Handles CRUD operations for Todo and Shopping lists, persisting to local storage via Flet.
