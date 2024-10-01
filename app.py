from flask import Flask, redirect, request, url_for, render_template_string, session, jsonify, Response
import requests
import os
import base64
from push_notion import push_data_to_notion
from utils import lifeos, generate_phase_image, find_database_ids_recursive
import threading
from flask_cors import CORS
import time
from datetime import datetime, timezone
import json
from shared_variables import redis_client


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'

CORS(app, resources={"*": {"origins": "*"}}) 


@app.route('/api/check_status', methods=['GET'])
def check_status():
    auth_header = request.headers.get('Authorization')
    access_token = auth_header.split(' ')[1]

    current_status = redis_client.get(access_token)
    if not current_status:
        redis_client.set(access_token, 'not_started')
        current_status = redis_client.get(access_token)
    
    return jsonify({"status": current_status.decode('utf-8')}), 200

def get_basic_auth_header(client_id, client_secret):
    client_credentials = f"{client_id}:{client_secret}"
    base64_encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
    return f"Basic {base64_encoded_credentials}"


@app.route('/api/process_data', methods=['POST'])
def process_data_api():
    data = request.json    
    access_token = data.get('access_token')
    user_text = data.get('user_text')
    act_key = data.get('act_key')
    template_id = data.get('template_id')
    redis_client.set(act_key, 'processing')
    print(template_id, access_token)

    processing_thread = threading.Thread(target=background_process_data, args=(access_token, user_text, act_key, template_id))
    processing_thread.start()
    
    # Return a response to Next.js
    return jsonify({"status": "processing_started"}), 200

def background_process_data(access_token, user_text, act_key, template_id):
    try:
        print("Background Task: Processing Started")        
        result = process_data(access_token, user_text, act_key, template_id)        
        print("Background Task: Processing Completed")
    
    except Exception as e:
        redis_client.set(act_key, 'not_started')
        print(f"Error during processing: {e}")


def process_data(access_token, user_text, act_key, template_id):
    print("STARTED PROCESS") 
    goalos_pid = template_id      
    print("Getting tasks..")
    data = lifeos(user_text)
    
    print("Getting tasks DONE")
    
    print("Getting database ids...")
    phases_db_id = find_database_ids_recursive(access_token, goalos_pid, "Phases")    
    tasks_db_id = find_database_ids_recursive(access_token, goalos_pid, "Tasks")    
    hidden_tasks_db_id = find_database_ids_recursive(access_token, goalos_pid, "Objectives")    
    sidequests_db_id = find_database_ids_recursive(access_token, goalos_pid, "Side Quests")    
    skills_db_id = find_database_ids_recursive(access_token, goalos_pid, "Skills")    
    print("Getting database ids DONE")
    
    # Iterate through the phases and generate images for each phase
    print("Generating images...")
    for phase in data["Phases"]:
        phase_img_url = generate_phase_image(phase["Phase"])  # Generate image for the phase        
        phase["phase_img_url"] = phase_img_url['images'][0]['url']  # Store image URL in the JSON data    
    print("Generated images.")    
    
    # Push data to Notion using the access token, database IDs, and the JSON data
    print("Pushing data to Notion...")
    push_data_to_notion(access_token, sidequests_db_id, phases_db_id, tasks_db_id, hidden_tasks_db_id, skills_db_id, data, act_key)
    redis_client.set(act_key, 'not_started')
    print("Pushed data!")
    
    return {"status": "completed"}

def search_notion_pages(access_token):
    url = "https://api.notion.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Send a POST request to the /search endpoint
    response = requests.post(url, headers=headers, json={"query": "Goal OS"})
    
    # Return the JSON response for debugging
    return response.json()

if __name__ == '__main__':
    app.run(threaded=True, debug=True, port=5001)