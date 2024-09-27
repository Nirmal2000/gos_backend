from openai import OpenAI
import fal_client
import requests

from dotenv import load_dotenv
import json
import time
from shared_variables import sse_clients, user_processing_status
load_dotenv()


client = OpenAI()


def send_event(access_token, data):    
    if access_token in sse_clients:
        user_processing_status[access_token] = data
        

def lifeos(goal):
    run = client.beta.threads.create_and_run(
        assistant_id="asst_GjRCGWoZDXmArmL1jPJhUVci",
        thread={
            "messages": [
            {"role": "user", "content": goal}
            ]
        }
    )
    threadid = run.thread_id
    runid = run.id

    while not run.status == "completed":        
        run = client.beta.threads.runs.retrieve(
            thread_id=threadid,
            run_id=runid
        )
        time.sleep(2)

    messages = client.beta.threads.messages.list(threadid)
    json_msg = json.loads(messages.to_json())    
    return json.loads(json_msg['data'][0]['content'][0]['text']['value'])


def generate_phase_image(prompt):

    handler = fal_client.submit(
        "fal-ai/flux/dev",
        arguments={
            "prompt": f'''Design a minimalistic cover image for a document titled '{prompt}' with a deep blue  color background. Use a playful hand-drawn, white font for the title in the center. Surround the text with simple, doodle-like white icons that relate to research and communication, such as magnifying glasses, bar charts, pie charts, data sheets, speech bubbles, and envelopes. The design should be clean, modern, and approachable, with soft pastel colors and a focus on clarity and simplicity to convey a professional yet friendly vibe.'''
        },
    )

    result = handler.get()
    return result


def get_page_blocks(access_token, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    response = requests.get(url, headers=headers)
    return response.json()

def delete_page(access_token, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.delete(url, headers=headers)
    return response.status_code

def find_database_ids_recursive(access_token, block_id, target_database_name):
    # Get the blocks (children) of the current block or page
    blocks = get_page_blocks(access_token, block_id)

    # Loop through each block and check if it's a database or has children to explore further
    for block in blocks['results']:
        block_type = block['type']

        # Check if the block is a database
        if block_type == 'child_database':
            database_title = block['child_database']['title']

            # Check if the database title matches the name we're looking for
            if database_title == target_database_name:
                print(f"Found database '{database_title}' with ID: {block['id']}")
                return block['id']

        # Recurse if the block has children
        if block['has_children']:
            child_block_id = block['id']
            # Recursive call to explore the child blocks
            result = find_database_ids_recursive(access_token, child_block_id, target_database_name)
            if result:
                return result  # Return as soon as we find the matching database

    return None



if __name__ == "__main__":
    # print(lifeos("How to ride a cycle"))

    print(find_database_ids_recursive('secret_anhY2TGVmu0pF2LatFAmZEAOaLxktD9spnLvhiIAtZe', '1081cb9f300b8128a389c43822202ff9', 'Side Quests'))