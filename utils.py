import fal_client
import httpx
from dotenv import load_dotenv
import json
import time
import os
import requests  # Add missing import
from shared_variables import redis_client
from prompt import SYSTEM_PROMPT, RESPONSE_SCHEMA
load_dotenv()


OPENROUTER_API_KEY = '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'

async def lifeos(goal):
    try:
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": goal}
                ]
            },
        ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'google/gemini-2.5-pro-preview-03-25',
                    'messages': messages,
                    'response_format': RESPONSE_SCHEMA,
                    'structured_outputs': True
                }
            )

        if not response.status_code == 200:
            raise Exception(f"OpenRouter API error: {response.status_code}")

        data = response.json()
        result = json.loads(data['choices'][0]['message']['content'])
        return result

    except Exception as e:
        print(f"Error in lifeos: {str(e)}")
        raise

# def lifeos(goal):
#     run = client.beta.threads.create_and_run(
#         assistant_id="asst_GjRCGWoZDXmArmL1jPJhUVci",
#         thread={
#             "messages": [
#             {"role": "user", "content": goal}
#             ]
#         }
#     )
#     threadid = run.thread_id
#     runid = run.id

#     while not run.status == "completed":        
#         run = client.beta.threads.runs.retrieve(
#             thread_id=threadid,
#             run_id=runid
#         )
#         time.sleep(1)

#     messages = client.beta.threads.messages.list(threadid)
#     json_msg = json.loads(messages.to_json())    
#     return json.loads(json_msg['data'][0]['content'][0]['text']['value'])

async def generate_phase_image(prompt):
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            if update and update.logs:
                for log in update.logs:
                    if log:
                        print(log["message"])

    result = await fal_client.subscribe_async(
        "fal-ai/flux/dev",
        arguments={
            "prompt": f'''Design a minimalistic cover image for a document titled '{prompt}' with a deep blue color background. Use a playful hand-drawn, white font for the title in the center. Surround the text with simple, doodle-like white icons that relate to research and communication, such as magnifying glasses, bar charts, pie charts, data sheets, speech bubbles, and envelopes. The design should be clean, modern, and approachable, with soft pastel colors and a focus on clarity and simplicity to convey a professional yet friendly vibe.'''
        },
        on_queue_update=on_queue_update,
    )
    print(result)
    return result



async def get_page_blocks(access_token, page_id):
    
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    timeout = httpx.Timeout(30.0, connect=20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers)
        a= response.json()        
        return a

async def delete_page(access_token, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    timeout = httpx.Timeout(30.0, connect=20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.delete(url, headers=headers)
        return response.status_code

async def find_database_ids_recursive(access_token, block_id, target_database_name):
    # Get the blocks (children) of the current block or page
    blocks = await get_page_blocks(access_token, block_id)
    
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
            result = await find_database_ids_recursive(access_token, child_block_id, target_database_name)
            if result:
                return result  # Return as soon as we find the matching database

    return None

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # test = await lifeos("How to ride a cycle")
        # print(test)
        
        result = await find_database_ids_recursive(
            # 'secret_bLnxlPo3hE5sZyKLoJIrOTGzwpMucXHnaFPP8knqxAr',
            'secret_EDNv7v3bEpqezxU4Inh02Rk3X5ejvLlNPFSfd4z5054',
            '1de1cb9f300b81e68aa6e7b7bf83ee47',
            'Side Quests'
        )
        print(result)

    asyncio.run(main())