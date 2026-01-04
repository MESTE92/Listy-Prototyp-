# Listy 📝✨

**Listy** is a modern, AI-powered To-Do and Shopping List application built with Python and [Flet](https://flet.dev/). It features a beautiful, theme-aware UI, voice input, and an intelligent assistant that helps you manage your lists.

![Listy Screenshot](assets/screenshots/screenshot1.png)
*(Place your screenshots in `assets/screenshots/`)*

## Features 🚀

- **Smart Organization**: Separate modes for To-Do tasks and Shopping lists.
- **AI Assistant 🤖**:  Chat with Gemini, OpenAI, or DeepSeek (via OpenRouter) to add items naturally (e.g., "Add ingredients for pizza").
- **Voice Input 🎙️**: Add tasks hands-free using your microphone.
- **Modern UI 🎨**: 
  - Dark/Light mode support (Lavender Theme).
  - Priority indicators (Red/Amber/Green).
  - Segmented views for filtering tasks.
- **Shopping Cart Mode 🛒**: Move items to the cart as you shop and clear them with one tap.
- **Privacy First**: All data and API keys are stored locally on your device.

## Installation 🛠️

### Prerequisites
- Python 3.10 or higher
- (Optional) Flutter SDK (only needed for building mobile apps)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/listy.git
   cd listy
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage ▶️

Run the app locally:
```bash
flet run main.py
```
Or simply:
```bash
python main.py
```

### AI Configuration
To use the AI features, click the **Settings (Gear Icon)** in the app header:
1. Select your provider (Google Gemini, OpenAI, or OpenRouter).
2. Enter your API Key.
   - *Note for OpenRouter:* You can leave the key empty to use the built-in standard key for free testing.

## Building executable 📦

**MacOS (.app / .dmg)**
```bash
flet pack main.py --name Listy --icon assets/icon.png
```

**Windows (.exe)**
(Run on a Windows machine)
```bash
flet pack main.py --name Listy --icon assets/icon.ico
```

## Architecture 🏗️

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed component diagram.

## License 📄

GNU Affero General Public License v3.0 (AGPLv3)
