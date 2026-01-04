# Voxo - YouTube Video Summarizer

A full-stack SaaS application that transforms YouTube videos into concise summaries with AI-powered text-to-speech capabilities.

## Features

- 🎥 Extract transcripts from YouTube videos
- 🤖 Generate structured summaries using Google Gemini 1.5 Flash
- 🔊 Convert summaries to speech using Amazon Polly Neural TTS
- 🎨 Modern, responsive UI built with Vite + React and Bootstrap
- 🐳 Dockerized for easy deployment

## Tech Stack

### Backend
- **FastAPI** (Python 3.12)
- **Google Gemini Pro** - AI summarization
- **Amazon Polly** - Neural text-to-speech
- **Supadata.ai** - YouTube transcript extraction

### Frontend
- **Vite + React** - Modern React build tool and framework
- **react-snap** - Pre-rendering for SEO optimization
- **Bootstrap 5** - CSS framework
- **Axios** - HTTP client

### Infrastructure
- **Docker Compose** - Container orchestration
- Multi-stage builds for optimized production images

## Prerequisites

- Docker and Docker Compose installed
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Supadata.ai API key ([Get one here](https://supadata.ai))
- AWS credentials with Polly access ([AWS Console](https://console.aws.amazon.com/))

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd Voxo
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPADATA_API_KEY=your_supadata_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
```

### 3. Build and Run with Docker Compose

```bash
docker-compose up --build
```

This will:
- Build both backend and frontend containers
- Start the backend server on port 8000
- Start the frontend server on port 5173

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)

## Usage

1. Open http://localhost:5173 in your browser
2. Paste a YouTube URL into the search bar
3. Click "Summarize"
4. Wait for the processing to complete
5. View the summary and listen to the audio narration

## API Endpoints

### POST `/api/summarize`

Summarize a YouTube video and convert to audio.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "summary": "Generated summary text...",
  "audio_base64": "base64_encoded_audio_data..."
}
```

## Development

### Running Backend Locally (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Running Frontend Locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

## Project Structure

```
Voxo/
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── globals.css
│   ├── index.html
│   ├── vite.config.js
│   ├── react-snap.json
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Troubleshooting

### Backend Issues

- **Port 8000 already in use**: Change the port in `docker-compose.yml`
- **API key errors**: Verify your `.env` file has correct credentials
- **Transcript errors**: Some videos may not have transcripts available

### Frontend Issues

- **Port 5173 already in use**: Change the port in `docker-compose.yml`
- **CORS errors**: Ensure backend CORS settings include your frontend URL
- **Connection errors**: Verify backend is running and accessible

## License

MIT License

