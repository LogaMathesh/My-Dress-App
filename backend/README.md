# Dress Classification API with Gemini

This backend application uses Google's Gemini AI to classify dress images based on position, style, and color.

## Features

- **Image Classification**: Analyzes dress images for position (upper/lower/full), style (formal/casual/traditional), and color
- **User Management**: Signup/login functionality
- **Image History**: Track uploaded images and classifications
- **Favorites**: Mark favorite outfits
- **Suggestions**: Get outfit suggestions based on destination
- **API Configuration**: Easy setup for Gemini API key

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Make sure PostgreSQL is running and create a database. Set these environment variables:

```bash
export DB_NAME="your_db_name"
export DB_USER="your_db_user" 
export DB_PASSWORD="your_db_password"
export DB_HOST="localhost"
export DB_PORT="5432"
```

### 3. Setup Gemini API Key

#### Option A: Use the setup script (Recommended)
```bash
python setup_api.py
```

Follow the prompts to enter your Gemini API key.

#### Option B: Manual configuration
1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Use the API endpoint:
   ```bash
   curl -X POST http://localhost:5000/config/api-key \
     -H "Content-Type: application/json" \
     -d '{"api_key": "your_api_key_here"}'
   ```

#### Option C: Environment variable
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /signup` - Create new user account
- `POST /login` - User login

### Image Classification
- `POST /classify` - Upload and classify dress image
- `POST /test-classification` - Test classification without saving

### Configuration
- `POST /config/api-key` - Set Gemini API key
- `GET /config/status` - Check configuration status  
- `POST /config/test-connection` - Test API connection

### User Data
- `GET /history/<username>` - Get user's upload history
- `POST /delete_upload` - Delete an uploaded image
- `POST /toggle_favorite` - Toggle favorite status
- `POST /get-suggestions` - Get outfit suggestions

### Utilities
- `GET /image/<filename>` - Serve uploaded images
- `GET /check-duplicates` - Check for duplicate uploads
- `POST /clean-duplicates` - Remove duplicate entries

## Configuration Files

- `config.py` - Configuration management
- `api_config.json` - Stores API key and settings (auto-generated)
- `gemini_client.py` - Gemini API client

## Classification Categories

### Position
- **upper**: Shirts, blouses, tops, t-shirts
- **lower**: Pants, skirts, trousers, shorts  
- **full**: Dresses, gowns, jumpsuits, sarees

### Style
- **formal**: Business attire, professional clothing, suits
- **casual**: Everyday clothing, relaxed wear, street wear
- **traditional**: Ethnic clothing, cultural dress, ceremonial wear

### Color
- Red, Blue, Green, Black, White, Yellow, Orange, Purple, Brown, Pink, Gray

## Migration from CLIP

This version replaces the previous CLIP-based classification with Gemini AI for better accuracy and more natural language understanding. The API endpoints remain the same for compatibility.

### Key Changes
- Removed `transformers` dependency
- Added `google-generativeai` dependency
- Improved classification accuracy with natural language prompts
- Added configuration management system
- Simplified classification logic

## Troubleshooting

### API Key Issues
- Ensure your Gemini API key is valid and has proper permissions
- Check the configuration status: `GET /config/status`
- Test the connection: `POST /config/test-connection`

### Database Issues
- Verify PostgreSQL is running
- Check database connection parameters
- Ensure the `uploads` and `users` tables exist

### Image Classification Issues
- Supported formats: PNG, JPG, JPEG, GIF, WEBP
- Maximum file size: 8MB
- Images are automatically converted to RGB format

## Development

To modify classification categories or prompts, edit:
- `config.py` - Default categories
- `gemini_client.py` - Classification prompts and logic

## Security Notes

- API keys are stored locally in `api_config.json`
- Use environment variables for production deployment
- Implement proper authentication for configuration endpoints in production