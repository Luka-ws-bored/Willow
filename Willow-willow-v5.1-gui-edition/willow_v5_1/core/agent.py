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
    def __init__(self, config):
        self.config = config
        self.primary = config.get("llm_provider", "openai")
        self.openai_key = config.get("openai_api_key", "")
        self.gemini_key = config.get("gemini_api_key", "")

        # Set up API keys
        if self.openai_key:
            self.openai = OpenAI(api_key=self.openai_key)
        else:
            self.openai = None
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)

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

    def generate_response(self, prompt):
        fallback_attempted = False

        # Attempt primary provider
        if self.primary == "openai" and self.openai_key:
            try:
                return self._ask_openai(prompt)
            except Exception as e:
                print("[!] OpenAI failed:", e)
                fallback_attempted = True

        if self.primary == "gemini" and self.gemini_key:
            try:
                return self._ask_gemini(prompt)
            except Exception as e:
                print("[!] Gemini failed:", e)
                fallback_attempted = True

        # Try fallback provider
        if fallback_attempted:
            if self.primary == "openai" and self.gemini_key:
                try:
                    return self._ask_gemini(prompt)
                except Exception as e:
                    print("[!] Gemini fallback failed:", e)
            elif self.primary == "gemini" and self.openai_key:
                try:
                    return self._ask_openai(prompt)
                except Exception as e:
                    print("[!] OpenAI fallback failed:", e)

        return "Error: All available LLM providers failed or are not configured properly."

    def _ask_openai(self, prompt):
        completion = self.openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()

    def _ask_gemini(self, prompt):
        # List available models for debugging (uncomment to print)
        # print(genai.list_models())
        model = genai.GenerativeModel("gemini-2.5-pro")  # Use a valid model ID
        response = model.generate_content(prompt)
        return response.text.strip()

    def process_prompt(self, prompt_text: str) -> str:
        """
        Processes the user prompt using the fallback logic.
        """
        logging.info(f"Processing prompt with fallback logic: '{prompt_text[:50]}...'")
        return self.generate_response(prompt_text)

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

    if (not agent.openai_key or agent.openai_key == "YOUR_OPENAI_API_KEY_HERE") and \
       (not agent.gemini_key or agent.gemini_key == "YOUR_GEMINI_API_KEY_HERE"):
        print("\nWARNING: API keys are not configured or are placeholders in .env.")
        print("LLM functionalities (ask, submit) will likely fail.")
        print("Please set valid API keys in willow_v5_1/.env\n")
        logging.warning("API keys missing or placeholders during CLI test run.")

    agent.run_cli()
