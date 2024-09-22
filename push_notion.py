import requests


# Function to create a page in a Notion database
def create_notion_page(database_id, properties, access_token, cover=None):
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

    response = requests.post(url, json=data, headers=HEADERS)
    return response.status_code, response.json()


def add_goal(goal, skills_gained, timeframe, goals_db_id, access_token):
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
    return create_notion_page(goals_db_id, properties, access_token)


def add_phase(phase, image_url, phases_db_id, access_token):
    
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
            "url": image_url  # URL to the image that you want to set as the cover
        }
    }
    
    # Create the phase page with properties
    return create_notion_page(phases_db_id, properties, access_token, cover)


def add_task(task, time, priority, skills, phase_relation, tasks_db_id, access_token):
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
            "multi_select": [{"name": skill} for skill in skills]
        },
        "Phases": {
            "relation": [{"id": phase_relation}]
        }
    }
    return create_notion_page(tasks_db_id, properties, access_token)


def add_hidden_task(hidden_task, main_task_relation, hidden_tasks_db_id, access_token):
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
    return create_notion_page(hidden_tasks_db_id, properties, access_token)


def add_side_task(task, sidequests_db_id, access_token):
    properties = {
        "Name": {
            "title": [
                {
                    "text": {"content": task['Task']}
                }
            ]
        },
        "Skills": {
            "multi_select": [{"name": skill} for skill in task['Skills']]
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
    return create_notion_page(sidequests_db_id, properties, access_token)


def push_data_to_notion(access_token, sidequests_db_id, phases_db_id, tasks_db_id, hidden_tasks_db_id, data):
    

    # 2. Add the phase
    for phase in data["Phases"]:
        phase_response = add_phase(
            phase=phase["Phase"],
            image_url=phase['phase_img_url'],
            phases_db_id=phases_db_id,
            access_token=access_token
        )
        print(phase_response)
        phase_id = phase_response[1]['id']  # The ID of the created phase

        # 3. Add the tasks
        for task_data in phase["Tasks"]:
            task_response = add_task(
                task=task_data["Task"],
                time=task_data["Time"],
                priority=task_data["Priority"],
                skills=task_data["Skills"],
                phase_relation=phase_id,
                tasks_db_id=tasks_db_id,
                access_token=access_token
            )
            print(task_response)
            task_id = task_response[1]['id']  # The ID of the created task
            # 4. Add the hidden tasks
            for hidden_task in task_data["HiddenTasks"]:
                add_hidden_task(
                    hidden_task=hidden_task,
                    main_task_relation=task_id,
                    hidden_tasks_db_id=hidden_tasks_db_id,
                    access_token=access_token
                )

    for sq in data['SideQuests']:
        add_side_task(sq, sidequests_db_id, access_token)        




if __name__ == "__main__":
    data = {
    "Goal": "Become a model",
    "Phases": [
        {
        "Phase": "Research and Preparation",
        "Tasks": [
            {
            "Task": "Research modeling agencies and types of modeling",
            "Time": "3 hours",
            "Priority": "High",
            "Skills": [
                "Market Research",
                "Industry Knowledge"
            ],
            "HiddenTasks": [
                "Compile a list of reputable modeling agencies",
                "Identify different types of modeling (fashion, commercial, etc.)"
            ]
            },
            {
            "Task": "Create a modeling portfolio",
            "Time": "10 hours",
            "Priority": "High",
            "Skills": [
                "Photography",
                "Branding"
            ],
            "HiddenTasks": [
                "Find a professional photographer",
                "Organize outfits and themes for the photo shoot",
                "Select and edit photos for the portfolio"
            ]
            },
            {
            "Task": "Develop a personal brand and online presence",
            "Time": "5 hours",
            "Priority": "Medium",
            "Skills": [
                "Social Media Management",
                "Personal Branding"
            ],
            "HiddenTasks": [
                "Create social media accounts (Instagram, LinkedIn)",
                "Post modeling-related content",
                "Engage with followers and industry professionals"
            ]
            }
        ]
        }
    ],
    "SideQuests": [
        {
        "Task": "Take a workshop on professional modeling techniques",
        "Time": "5 hours",
        "Priority": "Medium",
        "Skills": [
            "Modeling Techniques",
            "Confidence"
        ],
        "Resources": "Search for local modeling workshops or online courses on platforms like Skillshare or Udemy."
        },
        {
        "Task": "Read books on the modeling industry",
        "Time": "4 hours",
        "Priority": "Low",
        "Skills": [
            "Industry Knowledge"
        ],
        "Resources": "Consider books like 'The Model's Bible' by Paulina Porizkova or 'Modeling 101' by Ayelet Waldman."
        }
    ],
    "SkillsGained": [
        "Market Research",
        "Industry Knowledge",
        "Photography",
        "Branding",
        "Social Media Management",
        "Personal Branding"
    ],
    "Timeframe": "3 months"
    }
    # push_data_to_notion("secret_anhY2TGVmu0pF2LatFAmZEAOaLxktD9spnLvhiIAtZe",
    #                     'fff1cb9f-300b-818b-9427-c1f015fa0293',
    #                     "fff1cb9f-300b-8188-95e7-fa796ed31d8d",
    #                     "fff1cb9f-300b-8112-a4a7-cd77898577cc",
    #                     "fff1cb9f-300b-8147-a608-f65f161e7d78",
    #                     data
    #                     )
    
    print(add_phase("DAMN", 'https://fal.media/files/rabbit/ojZ6RyVbukPCKP5rRwXEV.png', '25c8ef29d7774465880c2eec622df454', 'secret_anhY2TGVmu0pF2LatFAmZEAOaLxktD9spnLvhiIAtZe'))