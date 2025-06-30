import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Environment variables for tests will be managed by setUp and tearDown

from willow_v5_1.core.agent import WillowAgent
from willow_v5_1.core.tasks import TaskManager

class TestWillowAgent(unittest.TestCase):

    def setUp(self):
        # Store original env vars and set test ones
        self.orig_openai_key = os.environ.get('OPENAI_API_KEY')
        self.orig_gemini_key = os.environ.get('GEMINI_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'test_setup_openai_key'
        os.environ['GEMINI_API_KEY'] = 'test_setup_gemini_key'

        # Mock dependencies that make external calls or rely on complex setup
        self.load_dotenv_patcher = patch('willow_v5_1.core.agent.load_dotenv')
        self.openai_patcher = patch('willow_v5_1.core.agent.openai')
        self.genai_patcher = patch('willow_v5_1.core.agent.genai')

        self.mock_load_dotenv = self.load_dotenv_patcher.start()
        self.mock_openai = self.openai_patcher.start()
        self.mock_genai = self.genai_patcher.start()

        # Setup dummy settings file
        self.base_dir = os.path.join(project_root, 'willow_v5_1')
        self.settings_path = os.path.join(self.base_dir, 'config/settings.json')
        self.backup_settings_path = self.settings_path + '.bak_agent_test'

        if os.path.exists(self.settings_path):
            os.rename(self.settings_path, self.backup_settings_path)

        os.makedirs(os.path.join(self.base_dir, 'config'), exist_ok=True)
        with open(self.settings_path, 'w') as f:
            json.dump({"api_preference": "openai", "theme": "dark"}, f)

        # Initialize agent AFTER patching and setting up env vars
        self.agent = WillowAgent()

        # Ensure genai.configure was called if API key was present from os.environ
        if os.environ.get('GEMINI_API_KEY'):
             self.mock_genai.configure.assert_called_with(api_key=os.environ['GEMINI_API_KEY'])

    def tearDown(self):
        # Stop patchers
        self.load_dotenv_patcher.stop()
        self.openai_patcher.stop()
        self.genai_patcher.stop()

        # Restore original settings file
        if os.path.exists(self.backup_settings_path):
            os.rename(self.backup_settings_path, self.settings_path)
        elif os.path.exists(self.settings_path):
            os.remove(self.settings_path)

        # Restore original env vars
        if self.orig_openai_key is not None:
            os.environ['OPENAI_API_KEY'] = self.orig_openai_key
        elif 'OPENAI_API_KEY' in os.environ: # if set by test and not originally present
            del os.environ['OPENAI_API_KEY']

        if self.orig_gemini_key is not None:
            os.environ['GEMINI_API_KEY'] = self.orig_gemini_key
        elif 'GEMINI_API_KEY' in os.environ: # if set by test and not originally present
            del os.environ['GEMINI_API_KEY']

    def test_agent_initialization(self):
        self.assertEqual(self.agent.openai_api_key, 'test_setup_openai_key')
        self.mock_openai.api_key = 'test_setup_openai_key' # Check if openai sdk key is set

        self.assertEqual(self.agent.gemini_api_key, 'test_setup_gemini_key')

        self.assertIsNotNone(self.agent.settings)
        self.assertEqual(self.agent.llm_preference, "openai")
        self.assertIsInstance(self.agent.task_manager, TaskManager)

    @patch('willow_v5_1.core.agent.WillowAgent._call_openai')
    def test_process_prompt_openai(self, mock_call_openai):
        self.agent.llm_preference = "openai"
        mock_call_openai.return_value = "OpenAI response"

        response = self.agent.process_prompt("Hello OpenAI")

        mock_call_openai.assert_called_once_with("Hello OpenAI")
        self.assertEqual(response, "OpenAI response")

    @patch('willow_v5_1.core.agent.WillowAgent._call_gemini')
    def test_process_prompt_gemini(self, mock_call_gemini):
        self.agent.llm_preference = "gemini"
        mock_call_gemini.return_value = "Gemini response"

        response = self.agent.process_prompt("Hello Gemini")

        mock_call_gemini.assert_called_once_with("Hello Gemini")
        self.assertEqual(response, "Gemini response")

    def test_process_prompt_unsupported_llm(self):
        self.agent.llm_preference = "unknown_llm"
        response = self.agent.process_prompt("Hello")
        self.assertIn("Error: LLM preference not supported", response)

    @patch('willow_v5_1.core.tasks.TaskManager.add_task')
    def test_submit_background_task_openai(self, mock_add_task):
        self.agent.llm_preference = "openai" # Does not directly affect submit_background_task type
        mock_add_task.return_value = 1 # Dummy task ID

        prompt_data = {'prompt': 'Long OpenAI task'}
        task_id = self.agent.submit_background_task("Test OpenAI Task", "openai_long", prompt_data)

        self.assertEqual(task_id, 1)
        mock_add_task.assert_called_once()
        args, kwargs = mock_add_task.call_args
        self.assertEqual(args[0], "Test OpenAI Task") # description
        self.assertEqual(args[1], self.agent._call_openai) # target_func
        self.assertEqual(args[2], "Long OpenAI task") # prompt_text_for_task argument

    @patch('willow_v5_1.core.tasks.TaskManager.add_task')
    def test_submit_background_task_gemini(self, mock_add_task):
        mock_add_task.return_value = 2

        prompt_data = {'prompt': 'Long Gemini task'}
        task_id = self.agent.submit_background_task("Test Gemini Task", "gemini_long", prompt_data)

        self.assertEqual(task_id, 2)
        mock_add_task.assert_called_once()
        args, kwargs = mock_add_task.call_args
        self.assertEqual(args[0], "Test Gemini Task")
        self.assertEqual(args[1], self.agent._call_gemini)
        self.assertEqual(args[2], "Long Gemini task")

    def test_submit_background_task_unknown_type(self):
        task_id = self.agent.submit_background_task("Test Unknown", "unknown_type", {'prompt': 'data'})
        self.assertEqual(task_id, -1) # Error indicator

    @patch('willow_v5_1.core.tasks.TaskManager.get_task_status')
    def test_get_task_status(self, mock_get_status):
        mock_get_status.return_value = {"status": "completed", "result": "Done"}

        status = self.agent.get_task_status(123)

        mock_get_status.assert_called_once_with(123)
        self.assertEqual(status, {"status": "completed", "result": "Done"})

    # Test actual OpenAI call if key is present and network is available (integration-like)
    # This is typically separated from unit tests or run conditionally
    @unittest.skipIf(not os.getenv("OPENAI_API_KEY_REAL") or os.getenv("OPENAI_API_KEY_REAL") == "sk-xxx", "Real OpenAI API key not provided or is placeholder")
    def test_real_openai_call(self):
        # This test requires a real (but temporary for test) OpenAI key
        # It also requires the `openai` library to not be mocked for this specific test
        # Setup: Ensure agent uses a real key for this test
        real_key_agent = WillowAgent()
        real_key_agent.openai_api_key = os.getenv("OPENAI_API_KEY_REAL")
        real_key_agent.llm_preference = "openai"
        openai.api_key = os.getenv("OPENAI_API_KEY_REAL") # Ensure SDK uses it too

        # Unpatch openai for this specific test if it was patched class-wide
        # This is tricky if setUpClass patched it. For instance-level, it might be okay.
        # A cleaner way is to not patch 'openai' in setUp if you have real call tests.

        with patch.object(real_key_agent, 'gemini_api_key', None): # Ensure no Gemini calls
            response = real_key_agent.process_prompt("What is the capital of France? (real test)")
            self.assertNotIn("Error", response)
            self.assertIsInstance(response, str)
            self.assertTrue(len(response) > 0)
            # A more specific assertion depends on expected model output, e.g. "Paris"
            # For now, just checking it runs without error and returns something.

if __name__ == '__main__':
    # If you want to run tests that use real API keys, set them as environment variables
    # e.g., OPENAI_API_KEY_REAL for the skipIf condition
    # For CI/CD, these would typically be secrets.
    # Example: os.environ["OPENAI_API_KEY_REAL"] = "your_actual_openai_key"
    unittest.main()
