import os
import uuid
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from typing import Optional
from datetime import datetime

load_dotenv()

app = FastAPI(title="Async AI Task Queue")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- In-memory job store ---
# This acts as our "database" of jobs
jobs = {}

# --- Models ---
class TaskRequest(BaseModel):
    task_type: str        # "summarize", "review", "rewrite"
    content: str          # the actual text to process

class JobStatus(BaseModel):
    job_id: str
    status: str           # "pending", "processing", "completed", "failed"
    result: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# --- AI worker function ---
async def process_ai_task(job_id: str, task_type: str, content: str):
    """This runs in the background — doesn't block the server"""
    try:
        # Mark job as processing
        jobs[job_id]["status"] = "processing"

        # Build prompt based on task type
        prompts = {
            "summarize": "Summarize the following text clearly and concisely in 3-5 sentences.",
            "review":    "Review the following text and give clear, actionable feedback on its quality, clarity, and improvements needed.",
            "rewrite":   "Rewrite the following text to be more professional, clear, and impactful."
        }

        system_prompt = prompts.get(task_type, prompts["summarize"])

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": content}
            ]
        )

        # Mark job as completed
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = response.choices[0].message.content
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        # Mark job as failed with error message
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

# --- Routes ---
@app.get("/")
def root():
    return {"status": "AI Task Queue is running", "total_jobs": len(jobs)}

@app.post("/submit_task")
async def submit_task(request: TaskRequest):
    """Submit a task — returns job_id immediately without waiting"""

    # Validate task type
    valid_types = ["summarize", "review", "rewrite"]
    if request.task_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_type. Choose from: {valid_types}"
        )

    # Create a unique job ID
    job_id = str(uuid.uuid4())

    # Store job in memory
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "task_type": request.task_type,
        "result": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }

    # Fire and forget — runs in background, doesn't block response
    asyncio.create_task(process_ai_task(job_id, request.task_type, request.content))

    # Return immediately with job ID
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Task submitted. Use /job_status/{job_id} to check progress."
    }

@app.get("/job_status/{job_id}")
def job_status(job_id: str):
    """Check the status of a submitted job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/all_jobs")
def all_jobs():
    """See all jobs and their statuses"""
    return {
        "total": len(jobs),
        "jobs": list(jobs.values())
    }

@app.delete("/clear_jobs")
def clear_jobs():
    """Clear all completed jobs from memory"""
    completed = [k for k, v in jobs.items() if v["status"] == "completed"]
    for k in completed:
        del jobs[k]
    return {"message": f"Cleared {len(completed)} completed jobs"}