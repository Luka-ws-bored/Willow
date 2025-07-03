from openai import OpenAI
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import logging
from .tasks import TaskManager # Import TaskManager using relative import
import time

# Configure logging (ensure it's configured once, e.g., in main.py or here if run standalone)
# If main.py already configures basicConfig, this might be redundant or could be adjusted.
# For simplicity, let's assume it's okay to call it here too, or it's handled.
if not logging.getLogger().hasHandlers(): # Check if root logger has handlers
    logging.basicConfig(filename='willow_v5_1/logs/app.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

class WillowAgent:
    def __init__(self):
        load_dotenv(dotenv_path='willow_v5_1/.env')
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.openai_api_key:
            logging.warning("OpenAI API key not found. OpenAI features will be unavailable.")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logging.info("OpenAI client initialized.")

        if not self.gemini_api_key:
            logging.warning("Gemini API key not found. Gemini features will be unavailable.")
        else:
            try:
                genai.configure(api_key=self.gemini_api_key)
                logging.info("Gemini API key configured.")
            except Exception as e:
                logging.error(f"Failed to configure Gemini API: {e}")


        self.settings = self.load_settings()
        self.llm_preference = self.settings.get("api_preference", "openai")
        logging.info(f"LLM preference set to: {self.llm_preference}")

        self.task_manager = TaskManager(max_concurrent_tasks=3) # Initialize TaskManager
        logging.info("TaskManager initialized within WillowAgent.")

    def load_settings(self):
        settings_path = 'willow_v5_1/config/settings.json'
        default_settings = {"theme": "dark", "font_size": 12, "api_preference": "openai"}
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    logging.info(f"Settings loaded from {settings_path}")
                    return settings
            else:
                logging.warning(f"Settings file not found at {settings_path}. Using default settings.")
                return default_settings
        except json.JSONDecodeError:
            logging.error(f"Error decoding {settings_path}. Using default settings.")
            return default_settings
        except Exception as e:
            logging.error(f"An unexpected error occurred loading settings: {e}. Using default settings.")
            return default_settings

    def _call_openai(self, prompt_text: str) -> str:
        if not self.openai_client:
            logging.error("OpenAI client is not configured.")
            return "Error: OpenAI client not configured."
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=150,
                temperature=0.7
            )
            logging.info(f"OpenAI API call successful for prompt: '{prompt_text[:50]}...'")
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "authentication" in str(e).lower():
                logging.error(f"OpenAI Authentication Error: {e}. Check your API key.")
                return "Error: OpenAI Authentication Failed. Please check your API key."
            elif "rate_limit" in str(e).lower():
                logging.error(f"OpenAI Rate Limit Error: {e}. Please check your usage and limits.")
                return "Error: OpenAI Rate Limit Exceeded. Please try again later."
            else:
                logging.error(f"Error calling OpenAI API: {e}")
                return f"Error processing with OpenAI: {e}"

    def _call_gemini(self, prompt_text: str) -> str:
        if not self.gemini_api_key:
            logging.error("Gemini API key is not configured.")
            return "Error: Gemini API key not configured."
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt_text)
            logging.info(f"Gemini API call successful for prompt: '{prompt_text[:50]}...'")
            return response.text
        except Exception as e: # Catching a broad exception, specific Gemini errors can be handled if known
            logging.error(f"Error calling Gemini API: {e}")
            # Check if the error is due to API key specifically if possible
            if "API_KEY_INVALID" in str(e) or "API_KEY_MISSING" in str(e): # Example check
                return "Error: Gemini API Key Invalid or Missing. Please check your configuration."
            return f"Error processing with Gemini: {e}"

    def process_prompt(self, prompt_text: str) -> str:
        """
        Processes the user prompt using the preferred LLM.
        This is a DIRECT, SYNCHRONOUS call for quick interactions.
        For longer tasks, use submit_background_task.
        """
        logging.info(f"Synchronously processing prompt with {self.llm_preference}: '{prompt_text[:50]}...'")

        if self.llm_preference == "openai":
            return self._call_openai(prompt_text)
        elif self.llm_preference == "gemini":
            return self._call_gemini(prompt_text)
        else:
            logging.warning(f"Unsupported LLM preference: {self.llm_preference}. Cannot process prompt.")
            return "Error: LLM preference not supported. Please check settings."

    def submit_background_task(self, description: str, task_type: str, prompt_data: dict) -> int:
        """
        Submits a task to be processed in the background by the TaskManager.
        task_type can be 'openai_long', 'gemini_long', or other custom task types.
        prompt_data contains necessary info for the task, e.g., {'prompt': 'some long prompt'}
        Returns the task_id.
        """
        logging.info(f"Submitting background task: '{description}' of type '{task_type}'")

        target_func = None
        if task_type == "openai_long":
            target_func = self._call_openai
        elif task_type == "gemini_long":
            target_func = self._call_gemini
        # Add more task types here, e.g., file operations, local searches
        # elif task_type == "local_file_search":
        #     target_func = self._local_file_search_function
        else:
            logging.error(f"Unknown task type for background submission: {task_type}")
            # Optionally raise an error or return a specific ID indicating failure
            return -1 # Indicate error or invalid task type

        if not target_func:
             logging.error(f"No target function resolved for task type {task_type}")
             return -1

        # Assuming prompt_data contains 'prompt' key for LLM tasks
        prompt_text_for_task = prompt_data.get('prompt', '')
        if not prompt_text_for_task and (task_type == "openai_long" or task_type == "gemini_long"):
            logging.error(f"Prompt data missing 'prompt' field for LLM task: {description}")
            return -1

        task_id = self.task_manager.add_task(
            description,
            target_func,
            prompt_text_for_task # Pass the prompt text as an argument to the target function
        )
        logging.info(f"Task '{description}' (ID: {task_id}) submitted to TaskManager.")
        return task_id

    def get_task_status(self, task_id: int):
        """Gets the status of a background task."""
        status = self.task_manager.get_task_status(task_id)
        logging.info(f"Fetching status for task ID {task_id}: {status}")
        return status

    def run_cli(self):
        """CLI mode for testing agent functionality, including background tasks."""
        print("Willow AI Assistant (CLI Mode with Task Manager)")
        print("Type 'exit' or 'quit' to end.")
        print("Commands:")
        print("  ask <prompt>                - Send a prompt for direct processing.")
        print("  submit <llm_type> <prompt>  - Submit a background task (e.g., submit openai_long Tell me a story).")
        print("  status <task_id>            - Check status of a background task.")
        print("  settings                      - View current settings.")

        while True:
            try:
                user_input = input("\nWillow-CLI > ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    logging.info("Exiting CLI mode.")
                    break

                parts = user_input.split(" ", 2)
                command = parts[0].lower()

                if command == "ask":
                    if len(parts) > 1:
                        prompt = parts[1] if len(parts) == 2 else parts[2] # if prompt has spaces
                        result = self.process_prompt(prompt)
                        print(f"[Direct Response] {result}")
                    else:
                        print("Usage: ask <your prompt>")

                elif command == "submit":
                    if len(parts) > 2:
                        task_type_cli = parts[1] # e.g. openai_long, gemini_long
                        prompt_cli = parts[2]
                        task_id_cli = self.submit_background_task(
                            description=f"CLI task: {prompt_cli[:30]}...",
                            task_type=task_type_cli,
                            prompt_data={'prompt': prompt_cli}
                        )
                        if task_id_cli != -1:
                            print(f"Task submitted with ID: {task_id_cli}")
                        else:
                            print("Failed to submit task. Check logs.")
                    else:
                        print("Usage: submit <openai_long|gemini_long> <your prompt for background task>")

                elif command == "status":
                    if len(parts) > 1:
                        try:
                            task_id_to_check = int(parts[1])
                            status_info = self.get_task_status(task_id_to_check)
                            if status_info:
                                print(f"[Task Status ID: {task_id_to_check}]")
                                for k, v in status_info.items():
                                    print(f"  {k}: {v}")
                            else:
                                print(f"No task found with ID: {task_id_to_check}")
                        except ValueError:
                            print("Invalid Task ID format. Please use a number.")
                    else:
                        print("Usage: status <task_id>")

                elif command == "settings":
                    print("[Current Settings]")
                    for k,v in self.settings.items():
                        print(f"  {k}: {v}")
                    print(f"  LLM Preference: {self.llm_preference}")

                else:
                    print("Unknown command. Available: ask, submit, status, settings, exit")

            except Exception as e:
                print(f"An error occurred in CLI loop: {e}")
                logging.error(f"CLI loop error: {e}", exc_info=True)


if __name__ == '__main__':
    print("Running WillowAgent CLI for testing...")
    logging.info("WillowAgent script run directly for CLI testing.")
    agent = WillowAgent()

    if (not agent.openai_api_key or agent.openai_api_key == "YOUR_OPENAI_API_KEY_HERE") and \
       (not agent.gemini_api_key or agent.gemini_api_key == "YOUR_GEMINI_API_KEY_HERE"):
        print("\nWARNING: API keys are not configured or are placeholders in .env.")
        print("LLM functionalities (ask, submit) will likely fail.")
        print("Please set valid API keys in willow_v5_1/.env\n")
        logging.warning("API keys missing or placeholders during CLI test run.")

    agent.run_cli()
