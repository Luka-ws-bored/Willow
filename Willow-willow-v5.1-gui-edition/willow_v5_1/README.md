# Willow AI Assistant (v5.1 - GUI Edition)

## Overview

Willow is a modular, offline-first capable AI assistant built in Python. It serves as a personal automation agent designed for local task execution, intelligent prompt processing via LLMs (OpenAI and Gemini), and features a user-friendly graphical interface built with PyQt6.

This version (v5.1) focuses on providing a stable GUI application that can interact with cloud-based LLMs, manage API keys securely, and handle potentially long-running tasks asynchronously to maintain a responsive user experience.

## Features

-   **Graphical User Interface (GUI):**
    -   Built with PyQt6 for a clean and lightweight user experience.
    -   Chat-style window for displaying user prompts and AI responses.
    -   Input field for submitting prompts.
    -   Asynchronous handling of AI requests to prevent UI freezing.
-   **LLM Integration:**
    -   Supports OpenAI (e.g., `text-davinci-003`) and Google Gemini Pro models.
    -   API preference can be configured in `config/settings.json`.
-   **Secure API Key Management:**
    -   API keys are loaded from a `.env` file (not committed to version control).
    -   An example `.env.example` file is provided.
-   **Configuration:**
    -   Basic application settings (like API preference) are managed in `config/settings.json`.
-   **Asynchronous Task Management:**
    -   Core `TaskManager` allows for background processing of tasks (e.g., complex API calls).
    -   This ensures the GUI remains responsive even during intensive operations.
    -   (Note: Full GUI integration for managing these tasks is a future enhancement).
-   **Logging:**
    -   Comprehensive logging to `logs/app.log` for debugging and monitoring.
-   **Modular Architecture:**
    -   Organized into `core`, `gui`, `config`, `logs`, and `prompts` directories for better maintainability.

## Project Structure

```
willow_v5_1/
├── main.py                # Application entry point, launches the GUI
├── core/
│   ├── agent.py          # WillowAgent class: handles LLM interaction, settings, task submission
│   └── tasks.py          # Task and TaskManager classes for async operations
├── gui/
│   └── main_window.py    # PyQt6 MainWindow class for the GUI
├── config/
│   ├── settings.json     # Application settings (e.g., API preference)
├── logs/
│   └── app.log           # Log file (created at runtime)
├── prompts/
│   └── default.md        # Placeholder for prompt templates
├── tests/                  # Unit tests (to be expanded)
│   ├── test_agent.py
│   └── test_config.py
├── .env                   # For API keys (create this from .env.example)
├── .env.example           # Example for .env file
├── AGENTS.md              # Detailed information for AI agents about the project
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Prerequisites

-   Python 3.10 or higher.
-   Access to OpenAI and/or Google Gemini API keys.

## Setup and Installation

1.  **Clone the repository (or ensure files are in place):**
    ```bash
    # If applicable
    # git clone <repository_url>
    # cd willow_v5_1
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    -   In the `willow_v5_1` directory, create a file named `.env`.
    -   Copy the contents of `.env.example` into `.env`.
    -   Replace the placeholder values with your actual OpenAI and Gemini API keys:
        ```env
        OPENAI_API_KEY="sk-your_openai_api_key_here"
        GEMINI_API_KEY="your_gemini_api_key_here"
        ```
    -   If you only plan to use one service, you can leave the other key blank, but the application might log warnings.

5.  **Review Configuration (Optional):**
    -   You can adjust settings like the default `api_preference` in `willow_v5_1/config/settings.json`.

## Running Willow

To start the Willow AI Assistant GUI application, run:

```bash
python main.py
```

This will launch the main window where you can type your prompts and receive responses from the configured AI model.

## CLI Mode (for testing core logic)

The `core/agent.py` script can also be run directly in a CLI mode for testing the agent's functionalities, including submitting background tasks and checking their status:

```bash
python core/agent.py
```
Follow the on-screen commands in CLI mode.

## Logging

Application activities, errors, and API interactions are logged in `willow_v5_1/logs/app.log`. This file is useful for troubleshooting.

## Contributing (for Jules or other AI Agents)

Please refer to `AGENTS.md` for detailed guidelines, capabilities, and areas for future enhancements. Key considerations:
-   Maintain Python 3.10+ compatibility.
-   Adhere to the existing modular structure.
-   Ensure UI responsiveness, especially for potentially blocking operations.
-   Update documentation (`README.md`, `AGENTS.md`) with any significant changes.

## Future Development

-   Full GUI integration for `TaskManager` (viewing task queue, statuses, results).
-   Menu bar for settings, log viewing, and other actions.
-   Implementation of local offline tasks (file operations, web searches, etc.).
-   Enhanced error display and recovery in the GUI.
-   Packaging as a standalone Windows application (e.g., using PyInstaller).
-   More sophisticated prompt engineering and context management.

---

Let the trees speak, let the agents rise.
> "The wind whispers Willow... and it obeys." - Luka-sama
