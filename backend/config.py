import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_file = Path(__file__).parent / 'api_config.json'
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default config."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                return self.default_config()
        else:
            return self.default_config()
    
    def default_config(self):
        """Create default configuration."""
        return {
            'gemini_api_key': '',
            'gemini_model': 'gemini-1.5-flash-latest',
            'max_image_size': 8 * 1024 * 1024,  # 8MB
            'classification_categories': {
                'position': ['upper', 'lower', 'full'],
                'style': ['formal', 'casual', 'traditional'],
                'color': ['red', 'blue', 'green', 'black', 'white', 'yellow', 'orange', 'purple', 'brown', 'pink', 'gray']
            }
        }
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_gemini_api_key(self):
        """Get Gemini API key from config or environment variable."""
        api_key = self.config.get('gemini_api_key', '')
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY', '')
        return api_key
    
    def set_gemini_api_key(self, api_key):
        """Set Gemini API key and save to config."""
        self.config['gemini_api_key'] = api_key
        return self.save_config()
    
    def get_gemini_model(self):
        """Get Gemini model name."""
        return self.config.get('gemini_model', 'gemini-1.5-flash-latest')
    
    def get_classification_categories(self):
        """Get classification categories."""
        return self.config.get('classification_categories', self.default_config()['classification_categories'])
    
    def is_configured(self):
        """Check if API key is configured."""
        return bool(self.get_gemini_api_key())

# Global config instance
config = Config()