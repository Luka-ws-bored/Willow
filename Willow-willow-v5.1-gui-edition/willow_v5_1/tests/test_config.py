import unittest
import os
import sys
import json

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from willow_v5_1.core.agent import WillowAgent  # Access agent to test its settings loading

class TestConfigLoading(unittest.TestCase):

    def setUp(self):
        # Create dummy settings and .env for testing
        # Paths are now relative to the willow_v5_1 directory, assuming test is run from project_root
        self.base_dir = os.path.join(project_root, 'willow_v5_1')
        self.test_settings_path = os.path.join(self.base_dir, 'config/test_settings.json')
        self.test_env_path = os.path.join(self.base_dir, '.test_env')
        self.actual_settings_path = os.path.join(self.base_dir, 'config/settings.json')
        self.actual_env_path = os.path.join(self.base_dir, '.env') # This is where agent.py loads from

        # Backup original files if they exist
        self.orig_settings_content = None
        if os.path.exists(self.actual_settings_path):
            with open(self.actual_settings_path, 'r') as f:
                self.orig_settings_content = f.read()

        self.orig_env_file_content = None # Content of the actual .env file
        if os.path.exists(self.actual_env_path):
            with open(self.actual_env_path, 'r') as f:
                self.orig_env_file_content = f.read()

        # Backup original environment variables if they are set
        self.orig_openai_env_var = os.environ.pop('OPENAI_API_KEY', None)
        self.orig_gemini_env_var = os.environ.pop('GEMINI_API_KEY', None)

        # Create test settings file
        os.makedirs(os.path.join(self.base_dir, 'config'), exist_ok=True)
        with open(self.test_settings_path, 'w') as f:
            json.dump({"theme": "test", "font_size": 10, "api_preference": "gemini"}, f)

        # Create test .env file
        with open(self.test_env_path, 'w') as f:
            f.write("OPENAI_API_KEY=test_openai_key\n")
            f.write("GEMINI_API_KEY=test_gemini_key\n")

    def tearDown(self):
        # Clean up dummy files
        if os.path.exists(self.test_settings_path):
            os.remove(self.test_settings_path)
        if os.path.exists(self.test_env_path):
            os.remove(self.test_env_path)

        # Restore original files
        if self.orig_settings_content:
            with open(self.actual_settings_path, 'w') as f:
                f.write(self.orig_settings_content)
        elif os.path.exists(self.actual_settings_path): # if it was created during test by mistake
            os.remove(self.actual_settings_path)

        # Restore original .env file if it existed
        if self.orig_env_file_content: # Corrected variable name here
            with open(self.actual_env_path, 'w') as f:
                f.write(self.orig_env_file_content)
        elif os.path.exists(self.actual_env_path): # If test created one and there was no original
            os.remove(self.actual_env_path)

        # Restore original environment variables
        if self.orig_openai_env_var is not None:
            os.environ['OPENAI_API_KEY'] = self.orig_openai_env_var
        elif 'OPENAI_API_KEY' in os.environ: # If it was set by test and not originally
             os.environ.pop('OPENAI_API_KEY', None)

        if self.orig_gemini_env_var is not None:
            os.environ['GEMINI_API_KEY'] = self.orig_gemini_env_var
        elif 'GEMINI_API_KEY' in os.environ: # If it was set by test and not originally
            os.environ.pop('GEMINI_API_KEY', None)

    def test_load_settings_from_file(self):
        # Temporarily rename actual settings to use test settings
        if os.path.exists(self.actual_settings_path):
            os.rename(self.actual_settings_path, self.actual_settings_path + '.bak')
        os.rename(self.test_settings_path, self.actual_settings_path)

        agent = WillowAgent() # Agent loads settings on init

        self.assertEqual(agent.settings.get("theme"), "test")
        self.assertEqual(agent.settings.get("api_preference"), "gemini")

        # Restore file names
        os.rename(self.actual_settings_path, self.test_settings_path)
        if os.path.exists(self.actual_settings_path + '.bak'):
            os.rename(self.actual_settings_path + '.bak', self.actual_settings_path)


    def test_load_api_keys_from_env(self):
         # Temporarily rename actual .env to use test .env
        if os.path.exists(self.actual_env_path):
            os.rename(self.actual_env_path, self.actual_env_path + '.bak_env_file') # distinguish

        # The self.test_env_path (containing test keys) should be renamed to self.actual_env_path
        # for the agent to load it.
        os.rename(self.test_env_path, self.actual_env_path)

        agent = WillowAgent() # Agent loads .env on init (which is now our test_env_path content)

        self.assertEqual(agent.openai_api_key, "test_openai_key") # Assert against keys from test_env_path
        self.assertEqual(agent.gemini_api_key, "test_gemini_key")

        # Clean up: remove the .env we created from test_env_path, then restore original if it existed
        os.remove(self.actual_env_path)
        if os.path.exists(self.actual_env_path + '.bak_env_file'):
            os.rename(self.actual_env_path + '.bak_env_file', self.actual_env_path)

    def test_default_settings_if_file_missing(self):
        # Pre-condition: Ensure settings file does not exist for this test
        if os.path.exists(self.actual_settings_path):
             os.rename(self.actual_settings_path, self.actual_settings_path + '.tmp_bak')

        agent = WillowAgent()
        self.assertEqual(agent.settings.get("api_preference"), "openai") # Default
        self.assertEqual(agent.settings.get("theme"), "dark") # Default

        # Restore if it was backed up
        if os.path.exists(self.actual_settings_path + '.tmp_bak'):
            os.rename(self.actual_settings_path + '.tmp_bak', self.actual_settings_path)


if __name__ == '__main__':
    unittest.main()
