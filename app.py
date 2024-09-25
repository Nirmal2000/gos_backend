from flask import Flask, redirect, request, url_for, render_template_string, session, jsonify
import requests
import os
import base64
from utils import find_database_ids_recursive
from push_notion import push_data_to_notion
from utils import lifeos, generate_phase_image
import threading
from flask_cors import CORS
import time
from datetime import datetime, timezone

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'

CORS(app)#, supports_credentials=True)#, origins=["https://localhost:3000"])

user_processing_status = {}
status_lock = threading.Lock()

def is_recent(created_time_str):
    """
    This function checks if the created_time is within 1 minute of the current time.
    """
    created_time = datetime.strptime(created_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    
    # Calculate the time difference in seconds
    time_difference = (current_time - created_time).total_seconds()
    
    # Check if the time difference is within 1 minute (60 seconds)
    return time_difference <= 60

def get_basic_auth_header(client_id, client_secret):
    client_credentials = f"{client_id}:{client_secret}"
    base64_encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
    return f"Basic {base64_encoded_credentials}"

# Home page with a "Connect to Notion" button

@app.route('/api/check_status', methods=['GET'])
def check_status():
    auth_header = request.headers.get('Authorization')
    access_token = auth_header.split(' ')[1]    

    # Safely access user_processing_status
    with status_lock:
        status = user_processing_status.get(access_token, 'not_started')
    
    print(access_token, status)
    return jsonify({"status": status}), 200

@app.route('/api/reset_status', methods=['POST'])
def reset_status():
    data = request.json
    access_token = data.get('access_token')

    if access_token:
        with status_lock:
            user_processing_status[access_token] = 'not_started'
        return jsonify({"status": "reset_successful"}), 200
    else:
        return jsonify({"error": "access_token missing"}), 400

@app.route('/api/process_data', methods=['POST'])
def process_data_api():
    data = request.json
    access_token = data.get('access_token')
    user_text = data.get('user_text')

    with status_lock:
        user_processing_status[access_token] = 'processing'

    processing_thread = threading.Thread(target=background_process_data, args=(access_token, user_text))
    processing_thread.start()
    
    # Return a response to Next.js
    return jsonify({"status": "processing_started"}), 200

def background_process_data(access_token, user_text):
    try:
        print("Background Task: Processing Started")
        # Perform heavy processing here
        result = process_data(access_token, user_text)
        
        # Update status to "completed" when done
        with status_lock:
            user_processing_status[access_token] = 'completed'
        
        print("Background Task: Processing Completed")
    
    except Exception as e:
        print(f"Error during processing: {e}")
        # In case of error, set status to "error"
        with status_lock:
            user_processing_status[access_token] = 'error'

def process_data(access_token, user_text):
    print("STARTED PROCESS")
    # After return from notion_callback, run search, find db ids and pass text
    
    search_res = search_notion_pages(access_token)['results']
    print(search_res)
    while not search_res or not is_recent(search_res[0]['created_time']):
        search_res = search_notion_pages(access_token)['results']
        time.sleep(1)
    goalos_pid = search_res[0]['id']
    phases_db_id = find_database_ids_recursive(access_token, goalos_pid, "Phases")
    tasks_db_id = find_database_ids_recursive(access_token, goalos_pid, "Tasks")
    hidden_tasks_db_id = find_database_ids_recursive(access_token, goalos_pid, "Objectives")
    sidequests_db_id = find_database_ids_recursive(access_token, goalos_pid, "Side Quests")
    skills_db_id = find_database_ids_recursive(access_token, goalos_pid, "Skills")
    
    # Generate JSON data using the lifeos function based on the user input    
    data = lifeos(user_text)    
    
    # Iterate through the phases and generate images for each phase
    for phase in data["Phases"]:
        phase_img_url = generate_phase_image(phase["Phase"])  # Generate image for the phase        
        phase["phase_img_url"] = phase_img_url['images'][0]['url']  # Store image URL in the JSON data
    
    # Push data to Notion using the access token, database IDs, and the JSON data
    push_data_to_notion(access_token, sidequests_db_id, phases_db_id, tasks_db_id, hidden_tasks_db_id, skills_db_id, data)
    
    return {"status": "completed"}

def search_notion_pages(access_token):
    url = "https://api.notion.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Send a POST request to the /search endpoint
    response = requests.post(url, headers=headers, json={"query": "Goal"})
    
    # Return the JSON response for debugging
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)