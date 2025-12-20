"""
Image classification service.
"""
from extensions.classifier import get_classifier
from flask import current_app

class ClassificationService:
    """Service for image classification using CLIP"""
    
    # Classification categories
    POSITION_CATEGORIES = [
        "upper body clothing, shirt, blouse, top",
        "lower body clothing, pants, skirt, trousers",
        "full body clothing, dress, gown, jumpsuit"
    ]
    
    STYLE_CATEGORIES = [
        "formal business attire, professional clothing, office wear",
        "traditional ethnic clothing, cultural dress, heritage wear",
        "casual everyday clothing, relaxed wear, comfortable outfit"
    ]
    
    COLOR_CATEGORIES = [
        "red clothing, red dress, red shirt",
        "blue clothing, blue dress, blue shirt", 
        "green clothing, green dress, green shirt",
        "black clothing, black dress, black shirt",
        "white clothing, white dress, white shirt",
        "yellow clothing, yellow dress, yellow shirt",
        "orange clothing, orange dress, orange shirt",
        "purple clothing, purple dress, purple shirt",
        "brown clothing, brown dress, brown shirt",
        "pink clothing, pink dress, pink shirt",
        "gray clothing, gray dress, gray shirt"
    ]
    
    @staticmethod
    def classify_all_attributes(image):
        """
        Efficiently classify all attributes in a single CLIP call.
        
        Args:
            image: PIL.Image object
            
        Returns:
            dict: {'position': str, 'style': str, 'color': str}
        """
        try:
            classifier = get_classifier()
            
            # Combine all categories into one comprehensive classification
            all_categories = []
            
            # Position categories
            all_categories.extend([
                "upper body shirt blouse top",
                "lower body pants skirt trousers", 
                "full body dress gown jumpsuit"
            ])
            
            # Style categories
            all_categories.extend([
                "formal business professional office",
                "traditional ethnic cultural heritage",
                "casual everyday relaxed comfortable"
            ])
            
            # Color categories
            all_categories.extend([
                "red clothing", "blue clothing", "green clothing",
                "black clothing", "white clothing", "yellow clothing",
                "orange clothing", "purple clothing", "brown clothing",
                "pink clothing", "gray clothing"
            ])
            
            # Single CLIP call for all categories
            results = classifier(images=image, candidate_labels=all_categories)
            
            if not results or len(results) == 0:
                return ClassificationService._get_defaults()
            
            # Sort by confidence score
            sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
            
            # Initialize results with defaults
            classification = ClassificationService._get_defaults()
            
            # Process results with very low threshold for better coverage
            for result in sorted_results:
                if result['score'] < 0.05:  # Very low threshold
                    continue
                    
                label = result['label'].lower()
                
                # Determine position
                if any(word in label for word in ["upper", "shirt", "blouse", "top", "t-shirt", "garment"]):
                    classification["position"] = "upper"
                elif any(word in label for word in ["lower", "pants", "skirt", "trousers", "jeans", "garment"]):
                    classification["position"] = "lower"
                elif any(word in label for word in ["full", "dress", "gown", "jumpsuit", "onesie", "garment"]):
                    classification["position"] = "full"
                
                # Determine style
                if any(word in label for word in ["formal", "business", "professional", "office", "corporate", "attire"]):
                    classification["style"] = "formal"
                elif any(word in label for word in ["traditional", "ethnic", "cultural", "heritage", "ceremonial"]):
                    classification["style"] = "traditional"
                elif any(word in label for word in ["casual", "everyday", "relaxed", "comfortable", "street", "outfit"]):
                    classification["style"] = "casual"
                
                # Determine color
                color_map = {
                    "red": "red", "blue": "blue", "green": "green",
                    "black": "black", "white": "white", "yellow": "yellow",
                    "orange": "orange", "purple": "purple", "brown": "brown",
                    "pink": "pink", "gray": "gray"
                }
                for color, clean_color in color_map.items():
                    if color in label:
                        classification["color"] = clean_color
                        break
            
            return classification
            
        except Exception as e:
            current_app.logger.error(f"Classification error: {e}")
            return ClassificationService._get_defaults()
    
    @staticmethod
    def _get_defaults():
        """Get default classification values"""
        return {"position": "upper", "style": "casual", "color": "black"}
    
    @staticmethod
    def classify_attribute(image, categories, clean=False):
        """Classify a single attribute using CLIP"""
        try:
            classifier = get_classifier()
            results = classifier(images=image, candidate_labels=categories)
            
            if results and len(results) > 0:
                sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
                top_result = sorted_results[0]
                
                if top_result['score'] > 0.05:
                    label = top_result['label']
                    
                    if clean:
                        return ClassificationService._clean_label(label, categories)
                    
                    return label
            
            # Return sensible defaults
            return ClassificationService._get_default_for_categories(categories)
            
        except Exception as e:
            current_app.logger.error(f"Classification error: {e}")
            return ClassificationService._get_default_for_categories(categories)
    
    @staticmethod
    def _clean_label(label, categories):
        """Clean and map label to simple format"""
        label_lower = label.lower()
        
        if "color" in categories[0].lower():
            color_map = {
                "red": "red", "blue": "blue", "green": "green", 
                "black": "black", "white": "white", "yellow": "yellow",
                "orange": "orange", "purple": "purple", "brown": "brown",
                "pink": "pink", "gray": "gray"
            }
            for color, clean_color in color_map.items():
                if color in label_lower:
                    return clean_color
            return "black"
        elif "clothing" in categories[0].lower() or "garment" in categories[0].lower():
            if any(word in label_lower for word in ["upper", "shirt", "blouse", "top", "t-shirt"]):
                return "upper"
            elif any(word in label_lower for word in ["lower", "pants", "skirt", "trousers", "jeans"]):
                return "lower"
            elif any(word in label_lower for word in ["full", "dress", "gown", "jumpsuit", "onesie"]):
                return "full"
            return "upper"
        elif any(word in categories[0].lower() for word in ["formal", "business", "professional"]):
            if any(word in label_lower for word in ["formal", "business", "professional", "office", "corporate", "attire"]):
                return "formal"
            elif any(word in label_lower for word in ["traditional", "ethnic", "cultural", "heritage", "ceremonial"]):
                return "traditional"
            elif any(word in label_lower for word in ["casual", "everyday", "relaxed", "comfortable", "street", "outfit"]):
                return "casual"
            return "casual"
        
        return "casual"
    
    @staticmethod
    def _get_default_for_categories(categories):
        """Get default value based on category type"""
        if "color" in categories[0].lower():
            return "black"
        elif "clothing" in categories[0].lower():
            return "upper"
        else:
            return "casual"





