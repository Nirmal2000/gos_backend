import httpx
import time
import json
from typing import Tuple, Dict, Any
import asyncio

heart_icons = [
    "❤️",  # Red heart
    "🧡",  # Orange heart
    "💛",  # Yellow heart
    "💚",  # Green heart
    "💙",  # Blue heart
    "💜",  # Purple heart
    "🖤",  # Black heart
    "🤍",  # White heart
    "🤎",  # Brown heart
    "💖",  # Sparkling pink heart
    "💗",  # Growing pink heart
    "💓",  # Beating pink heart
    "💞",  # Revolving pink heart
    "💕",  # Two pink hearts
    "💘",  # Heart with arrow
    "💝",  # Heart with ribbon
    "💟",  # Decorative heart
    "❣️",  # Heart exclamation
    "💔",  # Broken heart
    "❤️‍🔥"  # Heart on fire
]

async def create_notion_page(database_id, properties, access_token, cover=None, icon=None) -> Tuple[int, Dict[str, Any]]:
    print(f"Creating Notion page in database {database_id}")
    HEADERS = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    if cover:
        data["cover"] = cover
    if icon:
        data["icon"] = icon

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print('Request payload:', json.dumps(data, indent=2))
            response = await client.post(url, json=data, headers=HEADERS)
            status_code = response.status_code
            response_json = response.json()
            
            print(f"Response status: {status_code}")
            if status_code != 200:
                print(f"Error response: {json.dumps(response_json, indent=2)}")
                # Check for rate limiting
                if status_code == 429:
                    retry_after = int(response.headers.get('retry-after', 5))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    # Retry the request
                    response = await client.post(url, json=data, headers=HEADERS)
                    status_code = response.status_code
                    response_json = response.json()
            
            # Use asyncio.sleep instead of time.sleep in async functions
            await asyncio.sleep(0.5)
            return status_code, response_json
            
    except httpx.TimeoutException:
        print(f"Request timed out for database {database_id}")
        raise
    except Exception as e:
        print(f"Error creating page: {str(e)}")
        raise

async def add_goal(goal, skills_gained, timeframe, goals_db_id, access_token):
    properties = {
        "Goal": {
            "title": [
                {
                    "text": {"content": goal}
                }
            ]
        },
        "Skills Gained": {
            "multi_select": [{"name": skill} for skill in skills_gained]
        },
        "Timeframe": {
            "rich_text": [
                {
                    "text": {"content": timeframe}
                }
            ]
        }
    }
    return await create_notion_page(goals_db_id, properties, access_token)

async def add_phase(phase, image_url, phases_db_id, access_token, heart_icon):
    icon = {
        "type": "emoji",
        "emoji": heart_icon
    }
    
    properties = {
        "Name": {
            "title": [
                {
                    "text": {"content": phase}
                }
            ]
        }
    }
    cover = {
        "type": "external",
        "external": {
            "url": image_url
        }
    }
    
    return await create_notion_page(phases_db_id, properties, access_token, cover, icon)

async def add_skill_to_database(skill, skills_db_id, access_token):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": skills_db_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {"content": skill}
                    }
                ]
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code != 200:
                print(f"Error adding skill {skill}: {response.text}")
                raise Exception(f"Failed to add skill to database: {response.text}")
            return response.json().get('id')
    except Exception as e:
        print(f"Error adding skill {skill}: {str(e)}")
        raise

async def add_task(task, time, priority, skills, phase_relation, tasks_db_id, access_token, skill_dict, skills_db_id):
    skill_relations = []
    
    # Check if the skill is already in the dictionary, if not, add it
    for skill in skills:
        if skill in skill_dict:
            skill_id = skill_dict[skill]
        else:
            # If the skill is not in the dictionary, add it to the database and get the ID
            skill_id = await add_skill_to_database(skill, skills_db_id, access_token)
            skill_dict[skill] = skill_id  # Store the new skill in the dictionary
        
        # Append the skill ID to the relation
        skill_relations.append({"id": skill_id})

    properties = {
        "Name": {
            "title": [
                {
                    "text": {"content": task}
                }
            ]
        },
        "Time": {
            "rich_text": [
                {
                    "text": {"content": time}
                }
            ]
        },
        "Priority": {
            "select": {"name": priority}
        },
        "Skills": {
            "relation": skill_relations
        },
        "Phases": {
            "relation": [{"id": phase_relation}]
        }
    }
    return await create_notion_page(tasks_db_id, properties, access_token)

async def add_hidden_task(hidden_task, main_task_relation, hidden_tasks_db_id, access_token):
    properties = {
        "Name": {
            "title": [
                {
                    "text": {"content": hidden_task}
                }
            ]
        },
        "Tasks": {
            "relation": [{"id": main_task_relation}]
        }
    }
    return await create_notion_page(hidden_tasks_db_id, properties, access_token)

async def add_side_task(task, sidequests_db_id, access_token, skill_dict, skills_db_id):
    skill_relations = []
    
    # Check if the skill is already in the dictionary, if not, add it
    for skill in task['Skills']:
        if skill in skill_dict:
            skill_id = skill_dict[skill]
        else:
            # If the skill is not in the dictionary, add it to the database and get the ID
            skill_id = await add_skill_to_database(skill, skills_db_id, access_token)
            skill_dict[skill] = skill_id  # Store the new skill in the dictionary
        
        # Append the skill ID to the relation
        skill_relations.append({"id": skill_id})

    properties = {
        "Name": {
            "title": [
                {
                    "text": {"content": task['Task']}
                }
            ]
        },
        "Skills": {
            "relation": skill_relations
        },
        "Time": {
            "rich_text": [
                {
                    "text": {"content": task['Time']}
                }
            ]
        },
        "Priority": {
            "select": {"name": task['Priority']}
        },
        "Resources": {
            "rich_text": [
                {
                    "text": {"content": task['Resources']}
                }
            ]
        }
    }
    return await create_notion_page(sidequests_db_id, properties, access_token)

async def push_data_to_notion(access_token, sidequests_db_id, phases_db_id, tasks_db_id, hidden_tasks_db_id, skills_db_id, data, act_key):
    print("\nStarting data push to Notion...")
    skill_dict = {}
    try:
        # Add the phases
        increment = 40 // len(data['Phases'])
        tmpi = 0
        for i, phase in reversed(list(enumerate(data["Phases"]))):
            heart_icon = heart_icons[i % len(heart_icons)]
            print(f"\nProcessing phase: {phase['Phase']}")
            phase_response = await add_phase(
                phase=phase["Phase"],
                image_url=phase['phase_img_url'],
                phases_db_id=phases_db_id,
                access_token=access_token,
                heart_icon=heart_icon
            )
            
            phase_id = phase_response[1]['id']  # The ID of the created phase

            # Add the tasks
            for task_data in reversed(phase["Tasks"]):            
                print(f"Adding task: {task_data['Task']}")
                task_response = await add_task(
                    task=task_data["Task"],
                    time=task_data["Time"],
                    priority=task_data["Priority"],
                    skills=task_data["Skills"],
                    phase_relation=phase_id,
                    tasks_db_id=tasks_db_id,
                    access_token=access_token,
                    skill_dict=skill_dict,
                    skills_db_id=skills_db_id
                )
                
                task_id = task_response[1]['id']  # The ID of the created task
                # Add the hidden tasks
                for hidden_task in reversed(task_data["HiddenTasks"]):                         
                    print(f"Adding hidden task: {hidden_task}")
                    await add_hidden_task(
                        hidden_task=hidden_task,
                        main_task_relation=task_id,
                        hidden_tasks_db_id=hidden_tasks_db_id,
                        access_token=access_token
                    )

            cur_precent = 50 + (tmpi+1)*increment
            tmpi += 1        
            
        for sq in reversed(data['SideQuests']):
            print(f"\nAdding side quest: {sq['Task']}")
            await add_side_task(sq, sidequests_db_id, access_token, skill_dict, skills_db_id)
            
    except Exception as e:
        print(f"Error in push_data_to_notion: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example data
        data = {
            "Goal": "Become a model",
            "Phases": [
                {
                    "Phase": "Research and Preparation",
                    "Tasks": [
                        {
                            "Task": "Research modeling agencies",
                            "Time": "3 hours",
                            "Priority": "High",
                            "Skills": ["Market Research"],
                            "HiddenTasks": ["List agencies", "Compare fees"]
                        }
                    ]
                }
            ],
            "SideQuests": [],
            "SkillsGained": ["Market Research"],
            "Timeframe": "1 month"
        }
        
        # Test function calls here
        print("Running example data...")
        pass
    
    asyncio.run(main())
