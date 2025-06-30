import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.agent import WillowAgent # Import WillowAgent
import logging

if __name__ == "__main__":
    # Configure basic logging for the main application entry point as well
    # This ensures logs are captured even before the agent or GUI fully initializes.
    logging.basicConfig(filename='willow_v5_1/logs/app.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Application started.")

    app = QApplication(sys.argv)

    try:
        agent = WillowAgent()
        logging.info("WillowAgent initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize WillowAgent: {e}")
        # Optionally, show a critical error message to the user here if GUI can't even start
        # For now, we'll let it proceed, and errors will be logged.
        # A more robust solution might involve a fallback or an error dialog.
        # For this exercise, we assume agent initialization issues are logged and handled within agent/GUI.
        # If agent is critical for GUI to even show, this would need more handling.
        # However, our MainWindow can technically run with a non-functional agent (showing errors).
        # So, we create a placeholder if critical failure.
        class FailedAgent:
            def process_prompt(self, prompt):
                return "CRITICAL ERROR: Agent failed to initialize. Check logs."
        agent = FailedAgent()


    window = MainWindow(agent) # Pass the agent instance to the main window
    window.show()

    logging.info("MainWindow shown. Starting application event loop.")
    exit_code = app.exec()
    logging.info(f"Application exited with code {exit_code}.")
    sys.exit(exit_code)
