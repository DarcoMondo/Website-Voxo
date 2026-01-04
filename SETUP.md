# Quick Setup Guide

## Step 1: Create .env file

Create a `.env` file in the root directory with the following content:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPADATA_API_KEY=your_supadata_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
```

## Step 2: Get API Keys

### Google Gemini API Key
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

### Supadata.ai API Key
1. Visit https://supadata.ai
2. Sign up or log in
3. Get your API key from the dashboard
4. Copy the key to your `.env` file

### AWS Credentials
1. Go to AWS Console: https://console.aws.amazon.com/
2. Navigate to IAM → Users → Your User → Security Credentials
3. Create Access Keys if you don't have them
4. Ensure your AWS user has Polly permissions
5. Copy the Access Key ID and Secret Access Key to your `.env` file

## Step 3: Run the Application

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

