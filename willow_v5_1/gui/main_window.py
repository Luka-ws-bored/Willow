import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.agent import WillowAgent # Import WillowAgent
import logging

# Worker thread for handling agent processing
class AgentWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, agent, prompt):
        super().__init__()
        self.agent = agent
        self.prompt = prompt

    def run(self):
        try:
            response = self.agent.process_prompt(self.prompt)
            self.response_ready.emit(response)
        except Exception as e:
            logging.error(f"Error in agent worker thread: {e}")
            self.error_occurred.emit(str(e))


class MainWindow(QWidget):
    def __init__(self, agent: WillowAgent): # Accept agent instance
        super().__init__()
        self.agent = agent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Willow AI Assistant')
        self.setGeometry(100, 100, 700, 500) # Adjusted size

        layout = QVBoxLayout()

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-family: Consolas, Courier New, monospace;
                font-size: 10pt;
                border: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.response_area)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('Enter your prompt here...')
        self.input_field.returnPressed.connect(self.handle_send) # Send on Enter key
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #4f4f4f;
                padding: 5px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.input_field)

        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.handle_send)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)
        layout.addWidget(self.send_button)

        self.setLayout(layout)
        logging.info("MainWindow UI initialized.")

    def handle_send(self):
        user_input = self.input_field.text().strip()
        if user_input:
            self.response_area.append(f"<font color='#87CEEB'><b>User:</b></font> {user_input}\n")
            self.input_field.clear()
            self.response_area.append("<font color='#90EE90'><i>Willow: Processing...</i></font>\n")
            QApplication.processEvents() # Update UI to show "Processing..."

            # Disable input while processing
            self.input_field.setEnabled(False)
            self.send_button.setEnabled(False)

            # Run agent processing in a separate thread
            self.worker = AgentWorker(self.agent, user_input)
            self.worker.response_ready.connect(self.display_response)
            self.worker.error_occurred.connect(self.display_error)
            self.worker.finished.connect(self.on_processing_finished) # Re-enable input
            self.worker.start()

            logging.info(f"User input: {user_input}")

    def display_response(self, response_text):
        # Remove "Processing..." message (optional, a bit complex to do cleanly without direct line manipulation)
        # For simplicity, we'll just append. A more robust way would be to track the "Processing..." message.
        current_text = self.response_area.toHtml()
        if "<font color='#90EE90'><i>Willow: Processing...</i></font>" in current_text:
             # A simple way to replace the last line if it's the processing message
            lines = current_text.splitlines()
            if lines and "<font color='#90EE90'><i>Willow: Processing...</i></font>" in lines[-1]:
                self.response_area.setHtml("<br>".join(lines[:-1])) # Try to remove it

        self.response_area.append(f"<font color='#90EE90'><b>Willow:</b></font> {response_text}\n")
        self.response_area.verticalScrollBar().setValue(self.response_area.verticalScrollBar().maximum()) # Scroll to bottom
        logging.info(f"Agent response displayed: {response_text}")

    def display_error(self, error_message):
        current_text = self.response_area.toHtml()
        if "<font color='#90EE90'><i>Willow: Processing...</i></font>" in current_text:
            lines = current_text.splitlines()
            if lines and "<font color='#90EE90'><i>Willow: Processing...</i></font>" in lines[-1]:
                 self.response_area.setHtml("<br>".join(lines[:-1]))

        self.response_area.append(f"<font color='red'><b>Error:</b> {error_message}</font>\n")
        self.response_area.verticalScrollBar().setValue(self.response_area.verticalScrollBar().maximum())
        logging.error(f"Error displayed to user: {error_message}")

    def on_processing_finished(self):
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus() # Set focus back to input field
        logging.info("Processing finished, input re-enabled.")


if __name__ == '__main__':
    # This is for testing the GUI directly.
    # In the main application, main.py will instantiate WillowAgent and pass it.
    app = QApplication(sys.argv)

    # For standalone testing, create a dummy agent or a real one if keys are available
    # This ensures the GUI can run independently for quick tests.
    print("Running MainWindow directly for testing.")
    print("Attempting to initialize WillowAgent for standalone GUI test...")
    try:
        agent_for_test = WillowAgent()
        if not agent_for_test.openai_api_key and not agent_for_test.gemini_api_key:
            print("WARNING: API keys not found. LLM calls will fail in this test.")
            logging.warning("API keys not found for standalone GUI test.")
        else:
            print("WillowAgent initialized successfully with API keys for standalone test.")
    except Exception as e:
        print(f"Error initializing WillowAgent for test: {e}. GUI might not fully function.")
        logging.error(f"Error initializing WillowAgent for standalone GUI test: {e}")
        # Fallback to a dummy agent if WillowAgent fails to initialize
        class DummyAgent:
            def process_prompt(self, prompt):
                return f"Dummy response to: {prompt}"
        agent_for_test = DummyAgent()

    window = MainWindow(agent_for_test)
    window.show()
    sys.exit(app.exec())
