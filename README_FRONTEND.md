# 🎬 YouTube Comment Analyzer — Frontend

A modern **Next.js 16** frontend built with **TypeScript** and **React 19** that provides a sleek dashboard to analyze YouTube video comment sentiment powered by Google Gemini AI. Features Google OAuth2 login, YouTube account linking, and rich interactive analytics reports.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Google Sign-In** | Seamless OAuth2 authentication via `@react-oauth/google` |
| 🔗 **YouTube Account Linking** | Connect your YouTube account to enable personalized analysis |
| 🔍 **Video Search & Analysis** | Enter any YouTube URL or video ID to trigger AI-powered comment analysis |
| 📊 **Rich Analytics Report** | Visual breakdown of sentiment: Positive, Negative, Neutral, Questions, and Spam |
| ⚡ **Instant Cached Results** | Previously analyzed videos load instantly from the backend cache |
| 💨 **Server-Side Rendering** | Next.js App Router for optimal performance and SEO |

---

## 🗂️ Project Structure

```
youtube-comment-Analysis-frontend/
├── src/
│   ├── app/                  # Next.js App Router pages & layouts
│   ├── components/           # Reusable UI components
│   │   ├── GoogleAuthProviderWrapper.tsx  # OAuth provider setup
│   │   ├── GoogleLoginButton.tsx          # Google Sign-In button
│   │   ├── LinkYoutubeButton.tsx          # YouTube account linking
│   │   ├── SearchForm.tsx                 # Video URL/ID input form
│   │   └── ReportDisplay.tsx             # Full analytics report UI
│   └── types/                # Shared TypeScript type definitions
├── public/                   # Static assets
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Project metadata & scripts
└── .env                      # Environment variables (not committed)
```

---

## 🛠️ Prerequisites

- **Node.js 18+** (LTS recommended)
- **npm** or **yarn**
- The **backend server** running at `http://localhost:8000` → See the [Backend README](../youtube-comment-Analysis-backend/README.md)
- A **Google OAuth2 Client ID** → [Google Cloud Console](https://console.cloud.google.com/)

---

## 🚀 Installation & Setup

### 1. Clone & navigate to the frontend

```bash
git clone <your-repo-url>
cd youtube-comment-Analysis-frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env` file in the root of this directory:

```env
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
```

> ⚠️ **Note:** `NEXT_PUBLIC_*` variables are exposed to the browser. Never put secrets in variables with this prefix.

### 4. Start the development server

```bash
npm run dev
```

The app will start at **`http://localhost:3000`**

---

## 📜 Available Scripts

| Script | Command | Description |
|---|---|---|
| **Dev** | `npm run dev` | Start development server with hot-reload |
| **Build** | `npm run build` | Create an optimized production build |
| **Start** | `npm start` | Run the production build |
| **Lint** | `npm run lint` | Run ESLint for code quality checks |

---

## 🧩 Components Overview

### `GoogleAuthProviderWrapper.tsx`
Wraps the application with the `GoogleOAuthProvider` to make Google Sign-In available globally. Uses the `NEXT_PUBLIC_GOOGLE_CLIENT_ID` from your environment.

### `GoogleLoginButton.tsx`
A styled button that triggers the Google OAuth2 sign-in flow. Upon success, sends the Google credential token to the backend `/api/auth/google` endpoint and stores the returned JWT.

### `LinkYoutubeButton.tsx`
Enables users to link their YouTube account after logging in, allowing access to personalized channel data and history.

### `SearchForm.tsx`
The main input form where users enter a YouTube video URL or video ID. Handles URL parsing to extract the video ID before calling the backend analyze endpoint.

### `ReportDisplay.tsx`
The richest component — renders the complete analysis report including:
- Video metadata (title, thumbnail, views, likes)
- Sentiment breakdown with percentages
- Top keywords / trending topics
- Individual comment-level classifications

---

## 🔗 Connecting to the Backend

This frontend expects the backend to be running at the URL set in `BACKEND_URL` (defaults to `http://localhost:8000`).

All API calls are made using `axios`. Example flow:

```typescript
// SearchForm.tsx — trigger analysis
const response = await axios.get(`${process.env.BACKEND_URL}/api/analyze/${videoId}`);
const report = response.data;
```

Make sure the backend has CORS enabled for `http://localhost:3000`.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `next` 16 | React framework with App Router & SSR |
| `react` 19 | UI library |
| `typescript` | Type safety |
| `axios` | HTTP client for API calls |
| `@react-oauth/google` | Google OAuth2 sign-in integration |
| `jwt-decode` | Decode JWT tokens client-side |

---

## 🌐 Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `BACKEND_URL` | ✅ Yes | URL of the FastAPI backend (server-side only) |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | ✅ Yes | Google OAuth2 Client ID (browser-exposed) |

---

## 🤝 Full Stack Setup

To run the complete application, you need both services running:

```bash
# Terminal 1 — Backend
cd youtube-comment-Analysis-backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd youtube-comment-Analysis-frontend
npm run dev
```

Then open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## 📄 License

This project is for educational and personal use. See `LICENSE` for details.