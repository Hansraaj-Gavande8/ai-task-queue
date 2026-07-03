# Async AI Task Queue

A backend API built with FastAPI and Python asyncio that handles AI tasks asynchronously using a job queue pattern.

## What it does
Submit an AI task → get a job ID instantly → poll for results when ready.
No server blocking. No waiting. Just like real production AI backends work.

## Features
- Async task processing with Python asyncio
- Job status tracking (pending → processing → completed)
- Three AI task types: summarize, review, rewrite
- Powered by Groq LLM (llama-3.3-70b-versatile)
- Auto-generated Swagger UI at /docs

## Tech Stack
- Python
- FastAPI
- asyncio
- Groq LLM
- Pydantic
- python-dotenv

## Setup

1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file and add: `GROQ_API_KEY=your_key_here`
6. Run: `uvicorn main:app --reload`
7. Open: `http://127.0.0.1:8000/docs`

## API Endpoints
- `GET /` — Health check + total jobs count
- `POST /submit_task` — Submit an AI task, get job_id instantly
- `GET /job_status/{job_id}` — Check status of a specific job
- `GET /all_jobs` — View all jobs in the queue
- `DELETE /clear_jobs` — Clear completed jobs from memory

## How it works
1. Client submits task → server creates unique job_id and returns it immediately
2. AI processing runs in the background via asyncio.create_task()
3. Client polls /job_status/{job_id} until status is "completed"
4. Result is returned when ready