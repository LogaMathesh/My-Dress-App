# Chatbot Integration

This document describes the chatbot functionality integrated into the dress recommendation system.

## Overview

The chatbot uses CLIP (Contrastive Language-Image Pre-training) model to provide intelligent fashion recommendations based on text queries and user's uploaded images.

## Architecture

### Backend Components

1. **`embed_utils.py`** - CLIP model utilities for image and text embeddings
2. **`per_user_index.py`** - FAISS-based indexing system for each user
3. **`chatbot_routes.py`** - Flask routes for chatbot functionality
4. **`app.py`** - Main Flask app with chatbot blueprint integration

### Frontend Components

1. **`Chatbot.jsx`** - React component with modal interface
2. **`Home.jsx`** - Home page with floating chatbot icon
3. **`Home.css`** - Styling for chatbot modal and icon

## API Endpoints

### POST `/chatbot/query`
Query the chatbot for fashion recommendations.

**Request:**
```json
{
  "user_id": "string",
  "query": "string"
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "string",
      "style": "string", 
      "color": "string",
      "score": "float"
    }
  ],
  "query": "string",
  "count": "integer"
}
```

### POST `/chatbot/upload`
Upload an image for chatbot indexing.

**Request:**
- Form data with `image` file
- `user_id` (string)
- `style` (optional string)
- `color` (optional string)

### GET `/chatbot/status`
Check chatbot service status.

## Installation

1. Install additional dependencies:
```bash
pip install -r requirements_chatbot.txt
```

2. The system will automatically create necessary directories:
   - `indexes/` - FAISS index files
   - `uploaded_images/` - User uploaded images

## Usage

1. **Start the backend:**
```bash
python app.py
```

2. **Start the frontend:**
```bash
cd frontend/dress\ react
npm start
```

3. **Test the integration:**
```bash
python test_chatbot.py
```

## Features

- **Semantic Search**: Uses CLIP embeddings for intelligent image-text matching
- **Per-User Indexing**: Each user has their own FAISS index
- **Real-time Chat**: Modal-based chat interface
- **Image Upload**: Automatic indexing of uploaded images
- **Responsive Design**: Works on desktop and mobile

## Troubleshooting

1. **CUDA Issues**: If you don't have CUDA, the system will automatically use CPU
2. **Memory Issues**: Large CLIP model may require significant RAM
3. **Index Files**: User indexes are stored in `indexes/` directory
4. **Image Storage**: Uploaded images are stored in `uploaded_images/` directory

## Performance Notes

- First query may be slow due to model loading
- Subsequent queries are much faster
- Consider using GPU for better performance
- Index files are automatically created and managed
