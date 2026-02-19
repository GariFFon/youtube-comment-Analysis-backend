# YouTube Comment Analyzer - Backend

A powerful FastAPI backend that connects to the YouTube Data API and Google's Gemini AI to fetch videos and analyze comment sentiment, intent, and relevance at scale. All results are heavily cached and natively saved into MongoDB using the Beanie ODM.

## Features
- **YouTube Integration**: Fetches views, likes, comment counts, video thumbnails, channel names, and up to 100 top-level comments per video.
- **Gemini AI Engine**: Forces the `gemini-2.5-flash` model to return a strict Pydantic JSON structure categorizing comments into Positive, Negative, Neutral, Questions, and Spam.
- **Advanced Dashboard Metrics**: Calculates exact percentages and tracks the most discussed keywords/topics using Python's `Counter`.
- **Ultra-Fast MongoDB Caching**: Using `motor` and `beanie`, when a user analyzes a video, the entire massive report saves natively to a local database. The next user to search that video gets instant results without using API quotas or AI tokens.

## Prerequisites
- Python 3.9+
- A running MongoDB Database (Local `mongodb://localhost:27017` or Atlas cloud)
- [YouTube Data API Key](https://console.cloud.google.com/)
- [Gemini API Key](https://aistudio.google.com/)

## Installation

1. **Clone & CD into the directory**
```bash
cd youtube-comment-Analysis-backend
```

2. **Create a virtual environment (optional but recommended)**
```bash
python -m venv venv
source venv/bin/activate  # Mac / Linux
# venv\Scripts\activate   # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up your environment variables**
Ensure you have a `.env` file in the root directory:
```env
YOUTUBE_API_KEY=your_youtube_key_here
GEMINI_API_KEY=your_gemini_key_here
MONGO_URI=mongodb://localhost:27017/youtube_analyzer  # Or your Atlas URI
```

5. **Start the Development Server**
```bash
uvicorn app.main:app --reload
```

## How to connect your Frontend

Your backend server runs on `http://localhost:8000`. It already has CORS enabled to accept requests from your frontend.

### The Magic Endpoint
Make a simple `GET` request from your Frontend (React/Next.js/Vue) using `fetch` or `axios`:

```javascript
// Example Frontend API Call
const videoId = "wtLJPvx7-ys"; // Extract this from the YouTube URL

const response = await fetch(`http://localhost:8000/api/analyze/${videoId}`);
const analysisReport = await response.json();

console.log(analysisReport.video.title); // "Google I/O 2014 Keynote"
console.log(analysisReport.video.thumbnail_url); // "https://i.ytimg.com/vi/wtLJPvx7-ys/hqdefault.jpg"
console.log(analysisReport.positive_percentage); // 60.5
console.log(analysisReport.comments[0].analysis.classification); // "Positive (Praise / Satisfaction)"
```

### Force Refresh
If you want to ignore the MongoDB cache and force the AI to read new comments, just append `?force_refresh=true` to the URL.

## Interactive Documentation
To test the API manually without writing frontend code, visit the auto-generated Swagger UI:
�� **[http://localhost:8000/docs](http://localhost:8000/docs)**
