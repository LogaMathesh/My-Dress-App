import google.generativeai as genai
import base64
import io
from PIL import Image
import json
from config import config

class GeminiClassifier:
    def __init__(self):
        self.api_key = config.get_gemini_api_key()
        self.model_name = config.get_gemini_model()
        self.categories = config.get_classification_categories()
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
    
    def is_configured(self):
        """Check if the Gemini client is properly configured."""
        return self.model is not None and self.api_key
    
    def prepare_image(self, image):
        """Prepare PIL Image for Gemini API."""
        if isinstance(image, str):
            # If it's a file path, open the image
            image = Image.open(image)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def classify_dress_attributes(self, image):
        """
        Classify dress attributes using Gemini API.
        Returns a dictionary with position, style, and color.
        """
        if not self.is_configured():
            raise Exception("Gemini API not configured. Please set your API key.")
        
        try:
            prepared_image = self.prepare_image(image)
            
            # Create a detailed prompt for dress classification
            prompt = f"""
            Please analyze this clothing/dress image and classify it according to the following categories. 
            Return your response as a JSON object with exactly these keys: position, style, color.

            Categories to choose from:

            Position (body coverage):
            {', '.join(self.categories['position'])}
            - upper: shirts, blouses, tops, t-shirts (covers upper body)
            - lower: pants, skirts, trousers, shorts (covers lower body)  
            - full: dresses, gowns, jumpsuits, sarees (covers full body)

            Style (dress type):
            {', '.join(self.categories['style'])}
            - formal: business attire, professional clothing, office wear, suits
            - casual: everyday clothing, relaxed wear, comfortable outfits, street wear
            - traditional: ethnic clothing, cultural dress, ceremonial wear, heritage clothing

            Color (dominant color):
            {', '.join(self.categories['color'])}
            Choose the most prominent/dominant color you see in the clothing.

            Please respond with ONLY a JSON object in this exact format:
            {{
                "position": "one of the position values",
                "style": "one of the style values", 
                "color": "one of the color values"
            }}

            Look carefully at the image and choose the most appropriate category for each attribute.
            """
            
            response = self.model.generate_content([prompt, prepared_image])
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                classification = json.loads(response_text.strip())
                
                # Validate the response has required keys
                required_keys = ['position', 'style', 'color']
                for key in required_keys:
                    if key not in classification:
                        raise ValueError(f"Missing key: {key}")
                
                # Validate values are in allowed categories
                for key, value in classification.items():
                    if value not in self.categories[key]:
                        # If not in categories, use the first available option as default
                        classification[key] = self.categories[key][0]
                
                return classification
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing Gemini response: {e}")
                print(f"Raw response: {response_text}")
                # Return default values if parsing fails
                return {
                    "position": "upper",
                    "style": "casual", 
                    "color": "black"
                }
                
        except Exception as e:
            print(f"Error in Gemini classification: {e}")
            # Return default values if API call fails
            return {
                "position": "upper",
                "style": "casual",
                "color": "black"
            }
    
    def test_connection(self):
        """Test the Gemini API connection."""
        if not self.is_configured():
            return False, "API key not configured"
        
        try:
            # Create a simple test image
            test_image = Image.new('RGB', (100, 100), color='red')
            
            response = self.model.generate_content([
                "Describe this image in one sentence.",
                test_image
            ])
            
            return True, f"Connection successful: {response.text[:100]}..."
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

# Global classifier instance
gemini_classifier = GeminiClassifier()