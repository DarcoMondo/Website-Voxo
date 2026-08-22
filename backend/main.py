import os
import base64
import traceback
import re
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import google.generativeai as genai
import boto3

# --------------------
# SETUP
# --------------------
load_dotenv()

app = FastAPI(title="Voxo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# SUPADATA.AI (TRANSCRIPTION)
# --------------------
SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")
SUPADATA_API_URL = "https://api.supadata.ai/v1/transcript"

if SUPADATA_API_KEY:
    print("Supadata.ai API configured")
else:
    print("Warning: SUPADATA_API_KEY not configured")

# --------------------
# GEMINI (SUMMARY)
# --------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Names must match current Gemini API model codes (older IDs like gemini-1.5-* /
    # gemini-pro return 404). See https://ai.google.dev/gemini-api/docs/models
    model_names_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ]
    
    for model_name in model_names_to_try:
        try:
            print(f"Trying Gemini model: {model_name}")
            gemini_model = genai.GenerativeModel(model_name)
            # Test if model works
            test_response = gemini_model.generate_content("test")
            print(f"Successfully initialized Gemini model: {model_name}")
            break
        except Exception as e:
            print(f"Model {model_name} failed: {str(e)[:100]}")
            gemini_model = None
            continue
    
    if not gemini_model:
        print("Warning: Could not initialize any Gemini model")
else:
    print("Warning: GEMINI_API_KEY not configured")

# --------------------
# AWS POLLY (TTS)
# --------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

polly = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    try:
        polly = boto3.client(
            "polly",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        print("AWS Polly configured")
    except Exception as e:
        print(f"Warning: Could not initialize AWS Polly: {e}")
        polly = None
else:
    print("Warning: AWS credentials not configured")

# --------------------
# SUPPORTED LANGUAGES
# --------------------
# Single source of truth for languages offered to the user: display name
# (for the summary prompt) + AWS Polly neural voice (for the TTS).
SUPPORTED_LANGUAGES = {
    "it": {"name": "italiano", "voice": "Bianca"},
    "en": {"name": "english", "voice": "Joanna"},
    "es": {"name": "español", "voice": "Lucia"},
    "fr": {"name": "français", "voice": "Lea"},
    "de": {"name": "deutsch", "voice": "Vicki"},
    "pt": {"name": "português", "voice": "Camila"},
    "nl": {"name": "nederlands", "voice": "Laura"},
    "pl": {"name": "polski", "voice": "Ola"},
    "ru": {"name": "русский", "voice": "Tatyana"},
    "ja": {"name": "日本語", "voice": "Takumi"},
    "ko": {"name": "한국어", "voice": "Seoyeon"},
    "zh": {"name": "中文", "voice": "Zhiyu"},
    "hi": {"name": "हिंदी", "voice": "Aditi"},
    "ar": {"name": "العربية", "voice": "Zeina"},
    "tr": {"name": "türkçe", "voice": "Filiz"},
}

# --------------------
# MODELS
# --------------------
class SummarizeRequest(BaseModel):
    url: str
    # Language chosen by the user (must be a key in SUPPORTED_LANGUAGES).
    # There is no auto-detection: both the summary and the TTS audio are
    # always generated in this language, regardless of the video's language.
    language: str = "en"


class SummarizeResponse(BaseModel):
    summary: str
    audio_base64: str


# --------------------
# HELPERS
# --------------------
def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")


def chunk_text(text: str, max_chars: int):
    """Split text into chunks"""
    chunks, current = [], ""
    for sentence in text.split(". "):
        if len(current) + len(sentence) < max_chars:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks


def parse_supadata_response(result) -> str:
    """Parse response from Supadata.ai API, returns the transcript text"""
    # Extract transcript text from response
    if isinstance(result, dict):
        # Format: {'lang': 'en', 'availableLangs': [...], 'content': [{'lang': 'en', 'text': '...'}, ...]}
        if "content" in result and isinstance(result["content"], list):
            texts = []
            for item in result["content"]:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
            if texts:
                transcript = " ".join(texts)
                print(f"Transcript retrieved from content array: {len(transcript)} characters")
                return transcript

        # Try other possible response formats
        transcript = (
            result.get("transcript") or
            result.get("text") or
            result.get("transcription") or
            result.get("data", {}).get("transcript") or
            result.get("data", {}).get("text") or
            result.get("result", {}).get("transcript") or
            result.get("result", {}).get("text")
        )
        if transcript:
            # If transcript is a list of dicts with 'text' field
            if isinstance(transcript, list):
                texts = [item.get("text", "") if isinstance(item, dict) else str(item) for item in transcript]
                transcript = " ".join(texts)
            print(f"Transcript retrieved: {len(transcript)} characters")
            return transcript

    # If response is a list
    if isinstance(result, list) and len(result) > 0:
        texts = []
        for item in result:
            if isinstance(item, dict):
                text = item.get("text") or item.get("transcript") or item.get("transcription")
                if text:
                    texts.append(text)
            elif isinstance(item, str):
                texts.append(item)
        if texts:
            transcript = " ".join(texts)
            print(f"Transcript retrieved: {len(transcript)} characters")
            return transcript

    # If response is a string
    if isinstance(result, str):
        print(f"Transcript retrieved: {len(result)} characters")
        return result

    raise HTTPException(status_code=500, detail=f"Unexpected response format from Supadata.ai: {str(result)[:500]}")


# --------------------
# TRANSCRIPT (SUPADATA.AI)
# --------------------
def get_transcript(url: str) -> str:
    """Get transcript using Supadata.ai API, returns the transcript text"""
    if not SUPADATA_API_KEY:
        raise HTTPException(status_code=500, detail="SUPADATA_API_KEY not configured")
    
    try:
        video_id = extract_video_id(url)
        print(f"Getting transcript for video ID: {video_id} from Supadata.ai")
        
        # Supadata.ai uses x-api-key header (lowercase)
        headers = {
            "x-api-key": SUPADATA_API_KEY
        }
        
        last_error = None
        
        # Try GET with query parameters first (based on documentation example)
        api_url = "https://api.supadata.ai/v1/transcript"
        
        # Try GET with url parameter in query string
        try:
            print(f"Trying GET request with query parameter: url={url[:50]}...")
            response = requests.get(
                api_url,
                headers=headers,
                params={"url": url},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success with GET! Response type: {type(result)}")
                return parse_supadata_response(result)
            elif response.status_code == 401:
                last_error = f"401 Unauthorized - {response.text[:200]}"
            else:
                last_error = f"GET Status {response.status_code}: {response.text[:200]}"
        except requests.exceptions.RequestException as e:
            last_error = f"GET request failed: {str(e)}"
        
        # Try POST with JSON body
        headers["Content-Type"] = "application/json"
        payloads = [
            {"url": url},
            {"video_url": url},
            {"video_id": video_id},
        ]
        
        for payload in payloads:
            try:
                print(f"Trying POST with payload: {list(payload.keys())}")
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Success with POST! Response type: {type(result)}")
                    return parse_supadata_response(result)
                elif response.status_code == 401:
                    last_error = f"401 Unauthorized - {response.text[:200]}"
                    break
                elif response.status_code != 404:
                    last_error = f"POST Status {response.status_code}: {response.text[:200]}"
                    continue
            except requests.exceptions.RequestException as e:
                continue
        
        # If all failed, raise error
        if last_error:
            raise HTTPException(status_code=500, detail=f"Supadata.ai API error: {last_error}")
        else:
            raise HTTPException(status_code=404, detail="Supadata.ai API endpoint not found. Please check the API documentation.")
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=500, detail="Supadata.ai API timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Supadata.ai API error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting transcript: {str(e)}")


# --------------------
# SUMMARY (GEMINI)
# --------------------
def summarize_text(transcript: str, language: str) -> str:
    """Summarize text using Gemini, in the language chosen by the user"""
    if not gemini_model:
        raise HTTPException(status_code=500, detail="Gemini model not available. Please check GEMINI_API_KEY.")

    lang_name = SUPPORTED_LANGUAGES[language]["name"]

    try:
        chunks = chunk_text(transcript, 6000)
        partials = []

        for chunk in chunks:
            prompt = f"""Please summarize the following text. IMPORTANT: You MUST write the summary in {lang_name}, regardless of the language of the original text.

Requirements:
- Write the summary in {lang_name}
- Use clear paragraphs
- Be concise

Text to summarize:
{chunk}

Summary (in {lang_name}):"""
            resp = gemini_model.generate_content(prompt)
            partials.append(resp.text)

        if len(partials) == 1:
            return partials[0]

        final_prompt = f"""Combine and refine these summaries. IMPORTANT: Write the combined summary in {lang_name}, regardless of the language the summaries below are in.

Summaries to combine:
{chr(10).join(partials)}

Combined summary (in {lang_name}):"""
        final = gemini_model.generate_content(final_prompt)
        return final.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


# --------------------
# TTS (AWS POLLY)
# --------------------
def text_to_speech(text: str, language: str) -> str:
    """Synthesize speech for the summary using the Polly voice for the chosen language"""
    if not polly:
        raise HTTPException(status_code=500, detail="AWS Polly not configured. Please check AWS credentials.")

    voice_id = SUPPORTED_LANGUAGES[language]["voice"]
    print(f"Using AWS Polly voice: {voice_id} for language: {language}")

    audio = b""
    # Polly caps input length per request, so speech is generated chunk by
    # chunk and the resulting MP3 bytes are concatenated.
    for chunk in chunk_text(text, 2500):
        res = polly.synthesize_speech(
            Text=chunk,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine="neural",
        )
        audio += res["AudioStream"].read()

    return base64.b64encode(audio).decode()


# --------------------
# API
# --------------------
@app.get("/")
async def root():
    return {"message": "Voxo API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/languages")
async def list_languages():
    """List languages the frontend can offer in the language picker"""
    return {"languages": [{"code": code, "name": info["name"]} for code, info in SUPPORTED_LANGUAGES.items()]}


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    """Fetch the transcript, then summarize and narrate it in req.language"""
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language '{req.language}'")

    try:
        transcript = get_transcript(req.url)
        summary = summarize_text(transcript, req.language)
        audio = text_to_speech(summary, req.language)

        return SummarizeResponse(
            summary=summary,
            audio_base64=audio,
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
