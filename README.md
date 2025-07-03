# Willow
AI Agent Beta

A modular, offline-first capable AI assistant built in Python with PyQt6 GUI.

## Quick Start

Navigate to the `willow_v5_1/` directory for the main application.

See [willow_v5_1/README.md](willow_v5_1/README.md) for detailed setup instructions.

## Environment Cleanup

To ensure a clean development environment:

1. **Remove cached Python files:**
   ```bash
   find . -type f -name "*.pyc" -delete
   find . -type d -name "__pycache__" -exec rm -rf {} +
   ```

2. **Deactivate any existing virtual environments:**
   ```bash
   deactivate  # if using venv
   conda deactivate  # if using conda
   ```

3. **Create a fresh virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   venv\Scripts\activate  # On Windows
   ```
