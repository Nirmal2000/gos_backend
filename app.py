from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
import base64
from push_notion import push_data_to_notion
from utils import lifeos, generate_phase_image, find_database_ids_recursive
import asyncio
from datetime import datetime, timezone
import json
from shared_variables import redis_client
import httpx
# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_basic_auth_header(client_id: str, client_secret: str) -> str:
    client_credentials = f"{client_id}:{client_secret}"
    base64_encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
    return f"Basic {base64_encoded_credentials}"

# Pydantic models for request validation
class ProcessDataRequest(BaseModel):
    access_token: str
    user_text: str
    act_key: str
    template_id: str

async def process_data(access_token: str, user_text: str, act_key: str, template_id: str):
    print("access_token", access_token)
    print("user_text", user_text)
    print("act_key", act_key)
    print("template_id", template_id)
    print("STARTED PROCESS")
    goalos_pid = template_id
    print(goalos_pid)
    print("Getting tasks..")
    data = await lifeos(user_text)
    print(data)
    print("Getting tasks DONE")
    
    # Generate images for each phase
    print("Generating images...")
    for phase in data["Phases"]:
        phase_img_url = await generate_phase_image(phase["Phase"])
        phase["phase_img_url"] = phase_img_url['images'][0]['url']
    print("Generated images.")

    print("Getting database ids...")
    phases_db_id = await find_database_ids_recursive(access_token, goalos_pid, "Phases")
    tasks_db_id = await find_database_ids_recursive(access_token, goalos_pid, "Tasks")
    hidden_tasks_db_id = await find_database_ids_recursive(access_token, goalos_pid, "Objectives")
    sidequests_db_id = await find_database_ids_recursive(access_token, goalos_pid, "Side Quests")
    skills_db_id = await find_database_ids_recursive(access_token, goalos_pid, "Skills")
    print("Getting database ids DONE")
    
    # Push data to Notion
    print("Pushing data to Notion...")
    await push_data_to_notion(
        access_token, sidequests_db_id, phases_db_id, tasks_db_id,
        hidden_tasks_db_id, skills_db_id, data, act_key
    )
    print("Pushed data!")
    
    return {"status": "completed"}

@app.post("/api/process_data")
async def process_data_api(request: ProcessDataRequest):
    try:
        # Start the background task
        asyncio.create_task(process_data(
            request.access_token,
            request.user_text,
            request.act_key,
            request.template_id
        ))
        return {"status": "processing_started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def search_notion_pages(access_token: str):
    url = "https://api.notion.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json={"query": "Goal OS"}
        )
        return response.json()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)