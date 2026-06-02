# 🎬 YouTube Comment Analyzer — Backend

A high-performance **FastAPI** backend that integrates the **YouTube Data API v3** and **Google Gemini AI** to fetch videos and deeply analyze comment sentiment, intent, and relevance at scale. All results are cached natively in **MongoDB** using the Beanie ODM, with full Google OAuth2 authentication support.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎥 **YouTube Integration** | Fetches video metadata: title, views, likes, comment counts, thumbnails, and up to 100 top-level comments |
| 🤖 **Gemini AI Engine** | Uses `gemini-2.5-flash` to return a structured Pydantic JSON response classifying comments |
| 📊 **Advanced Dashboard Metrics** | Calculates exact sentiment percentages and tracks top discussed keywords/topics via Python `Counter` |
| ⚡ **Ultra-Fast MongoDB Caching** | Analyzed reports are saved with `motor` + `beanie` — subsequent requests return instantly, saving API quota |
| 🔐 **Google OAuth2 Auth** | Secure JWT-based authentication using Google Sign-In |
| 📝 **Auto Swagger Docs** | Interactive API documentation auto-generated at `/docs` |

---

## 🗂️ Project Structure

```
youtube-comment-Analysis-backend/
├── app/
│   ├── main.py          # FastAPI app entry point & lifespan
│   ├── api/             # Route handlers (analyze, auth, etc.)
│   ├── core/            # Config, security, DB connection
│   ├── models/          # Beanie/Pydantic MongoDB models
│   └── services/        # YouTube API & Gemini AI service logic
├── tests/               # Pytest test suite
├── test_yt.py           # Quick YouTube API sanity test
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (not committed)
```

---

## 🛠️ Prerequisites

- **Python 3.9+**
- **MongoDB** running locally (`mongodb://localhost:27017`) or a cloud Atlas URI
- A **YouTube Data API v3 Key** → [Get one here](https://console.cloud.google.com/)
- A **Gemini API Key** → [Get one here](https://aistudio.google.com/)
- A **Google OAuth2 Client ID** (for login) → [Google Cloud Console](https://console.cloud.google.com/)

---

## 🚀 Installation & Setup

### 1. Clone & navigate to the backend

```bash
git clone <your-repo-url>
cd youtube-comment-Analysis-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root of this directory:

```env
YOUTUBE_API_KEY=your_youtube_data_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017/youtube_analyzer
GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
SECRET_KEY=your_jwt_secret_key_here
```

### 5. Start the development server

```bash
uvicorn app.main:app --reload
```

The server will start at **`http://localhost:8000`**

---

## 📡 API Endpoints

### Analyze a Video

```http
GET /api/analyze/{video_id}
```

| Parameter | Type | Description |
|---|---|---|
| `video_id` | `string` (path) | YouTube video ID (e.g., `wtLJPvx7-ys`) |
| `force_refresh` | `boolean` (query) | Skip cache and re-fetch from YouTube + Gemini AI |

**Example Response:**
```json
{
  "video": {
    "title": "Google I/O 2014 Keynote",
    "thumbnail_url": "https://i.ytimg.com/vi/wtLJPvx7-ys/hqdefault.jpg",
    "view_count": 1200000,
    "like_count": 45000
  },
  "positive_percentage": 60.5,
  "negative_percentage": 15.2,
  "neutral_percentage": 18.0,
  "question_percentage": 5.3,
  "spam_percentage": 1.0,
  "top_keywords": ["amazing", "keynote", "android"],
  "comments": [
    {
      "text": "This is incredible!",
      "analysis": {
        "classification": "Positive (Praise / Satisfaction)",
        "reasoning": "User expresses enthusiastic approval."
      }
    }
  ]
}
```

### Force Refresh (bypass cache)

```http
GET /api/analyze/{video_id}?force_refresh=true
```

### Authentication

```http
POST /api/auth/google    # Google OAuth2 sign-in, returns JWT
GET  /api/auth/me        # Get current authenticated user info
```

---

## 🧪 Testing

```bash
# Run the full test suite
pytest tests/

# Quick YouTube API connectivity test
python test_yt.py
```

---

## 🔗 Connecting with the Frontend

Your backend runs on `http://localhost:8000` and has CORS pre-configured to accept requests from the Next.js frontend.

**Example frontend fetch:**
```javascript
const videoId = "wtLJPvx7-ys";
const response = await fetch(`http://localhost:8000/api/analyze/${videoId}`);
const report = await response.json();

console.log(report.video.title);              // "Google I/O 2014 Keynote"
console.log(report.positive_percentage);      // 60.5
console.log(report.comments[0].analysis.classification); // "Positive (Praise / Satisfaction)"
```

---

## 📖 Interactive API Documentation

Visit the auto-generated Swagger UI to test all endpoints without writing any code:

🔗 **[http://localhost:8000/docs](http://localhost:8000/docs)**

Or the ReDoc alternative:

🔗 **[http://localhost:8000/redoc](http://localhost:8000/redoc)**

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `motor` + `beanie` | Async MongoDB ODM |
| `google-api-python-client` | YouTube Data API v3 |
| `google-genai` | Gemini AI SDK |
| `pyjwt` + `passlib` | JWT authentication |
| `pydantic` + `pydantic-settings` | Data validation & config |
| `python-dotenv` | Environment variable loading |

---

## 📄 License

This project is for educational and personal use. See `LICENSE` for details.
