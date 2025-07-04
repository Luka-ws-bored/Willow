# AGENTS.md

## Agent Name: Willow (Version 5.1 - GUI Edition)

## Purpose
Willow is a personal, offline-first capable AI assistant designed for modular task execution, automation, and local/cloud AI workflows. This version introduces a PyQt6-based graphical user interface (GUI) and enhances its core functionalities.

## Capabilities
- **GUI Interaction:**
    - User input via a dedicated text field.
    - Scrollable chat-style display for prompts and responses.
    - Asynchronous processing of LLM requests to keep the GUI responsive.
- **LLM Integration:**
    - Supports both OpenAI (e.g., text-davinci-003) and Google Gemini Pro models.
    - API keys are managed via a `.env` file.
    - Model preference can be set in `config/settings.json`.
- **Configuration:**
    - API keys stored in `.env` (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`).
    - Application settings (theme, font size, API preference) in `config/settings.json`.
- **Asynchronous Task Handling (Core Logic):**
    - `TaskManager` class for managing background tasks (e.g., longer API calls).
    - Tasks are processed in separate threads.
    - Conceptual support for queuing and status checking of tasks (demonstrated in CLI mode, not yet fully integrated into GUI for status display).
- **Logging:**
    - Detailed logging of application events, API calls, errors, and task statuses to `logs/app.log`.
- **Modularity:**
    - Code is structured into `core` (agent logic, tasks), `gui` (UI components), `config` (settings, keys), `prompts`, and `logs`.

## Core Components
- `main.py`: Entry point for the application, initializes and launches the GUI.
- `gui/main_window.py`: Defines the PyQt6 main window, handles UI elements and user interaction.
- `core/agent.py`: `WillowAgent` class containing the main logic for processing prompts, interacting with LLMs, and managing tasks.
- `core/tasks.py`: `Task` and `TaskManager` classes for asynchronous operation handling.
- `config/settings.json`: Stores user-configurable settings.
- `.env`: Stores API keys (gitignored, use `.env.example` as a template).
- `logs/app.log`: Application log file.

## How to Run
1.  Ensure Python 3.10+ is installed.
2.  Create a virtual environment (recommended).
3.  Install dependencies: `pip install -r requirements.txt`
4.  Create a `.env` file in the `willow_v5_1` directory by copying `.env.example` and fill in your actual API keys for OpenAI and/or Gemini.
5.  Run the application: `python main.py`

## Future Enhancements (Potential for Jules or further development)
- Full GUI integration for `TaskManager` (displaying task statuses, managing queue).
- Menu bar in GUI for accessing settings, logs, etc.
- Implementation of actual local tasks (file ops, search) via `TaskManager`.
- More robust error handling and user feedback in the GUI.
- Packaging into a standalone Windows executable.
- Advanced prompt chaining and memory features.
- TTS for audio changelogs or responses.
- Customizable themes for the GUI.
