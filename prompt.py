RESPONSE_SCHEMA = {
  "type": "json_schema",
  "json_schema": {
    "name": "goal-os-schema",
    "strict": True,
    "schema": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "Goal": {
          "type": "string",
          "description": "The main goal for the project"
        },
        "Phases": {
          "type": "array",
          "description": "The different phases for achieving the goal",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "Phase": {
                "type": "string",
                "description": "The phase of the process"
              },
              "Tasks": {
                "type": "array",
                "description": "The tasks related to the phase",
                "items": {
                  "type": "object",
                  "additionalProperties": False,
                  "properties": {
                    "Task": {
                      "type": "string",
                      "description": "A specific task to be completed"
                    },
                    "Time": {
                      "type": "string",
                      "description": "The estimated time required to complete the task"
                    },
                    "Priority": {
                      "type": "string",
                      "description": "The priority level of the task (High, Medium, Low)",
                      "enum": [
                        "High",
                        "Medium",
                        "Low"
                      ]
                    },
                    "Skills": {
                      "type": "array",
                      "description": "Skills required to complete the task",
                      "items": {
                        "type": "string"
                      }
                    },
                    "HiddenTasks": {
                      "type": "array",
                      "description": "The smaller hidden tasks under the main task",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": [
                    "Task",
                    "Time",
                    "Priority",
                    "Skills",
                    "HiddenTasks"
                  ]
                }
              }
            },
            "required": [
              "Phase",
              "Tasks"
            ]
          }
        },
        "SideQuests": {
          "type": "array",
          "description": "Optional side tasks to support the main tasks and enhance skills",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "Task": {
                "type": "string",
                "description": "A side quest task to improve skills"
              },
              "Time": {
                "type": "string",
                "description": "The estimated time required to complete the side quest"
              },
              "Priority": {
                "type": "string",
                "description": "The priority level of the side quest",
                "enum": [
                  "High",
                  "Medium",
                  "Low"
                ]
              },
              "Skills": {
                "type": "array",
                "description": "Skills to be improved by completing the side quest",
                "items": {
                  "type": "string"
                }
              },
              "Resources": {
                "type": "string",
                "description": "Resources or links to help complete the side quest"
              }
            },
            "required": [
              "Task",
              "Time",
              "Priority",
              "Skills",
              "Resources"
            ]
          }
        },
        "SkillsGained": {
          "type": "array",
          "description": "Skills that will be gained after completing the main tasks",
          "items": {
            "type": "string"
          }
        },
        "Timeframe": {
          "type": "string",
          "description": "The overall timeframe for completing all tasks"
        }
      },
      "required": [
        "Goal",
        "Phases",
        "SideQuests",
        "SkillsGained",
        "Timeframe"
      ]
    }
  }
}

SYSTEM_PROMPT = '''Goal OS Assistant

System Instructions
You help users break down their big goals into small, actionable tasks, creating a clear roadmap for them to follow. Your response must follow a specific JSON schema structure with the following components:

1. Goal (Required)
   - A clear, concise statement of the main objective
   - Example: "Launch an e-commerce website for handmade jewelry"

2. Phases (Required)
   - A series of sequential stages to achieve the goal
   - Each phase contains:
     * Phase name (e.g., "Research", "Planning", "Implementation", "Testing", "Launch", "Monitoring")
     * Tasks array with detailed information for each task:
       - Task: Clear, specific action
       - Time: Estimated completion time (e.g., "2 hours", "3 days")
       - Priority: "High", "Medium", or "Low"
       - Skills: Array of required or developed skills
       - HiddenTasks: Array of smaller subtasks that break down the main task

3. SideQuests (Required)
   - Optional tasks to enhance skills relevant to the goal
   - Each side quest includes:
     * Task: Clear description of the learning activity
     * Time: Estimated completion time
     * Priority: "High", "Medium", or "Low"
     * Skills: Array of skills to be improved
     * Resources: Links or materials needed for completion

4. SkillsGained (Required)
   - Array of all skills that will be developed through completing the tasks
   - Example: ["Market Research", "Web Development", "SEO", "Content Writing"]

5. Timeframe (Required)
   - Overall estimated duration to complete all phases
   - Format as a clear time period (e.g., "3 months", "6 weeks")

Input Process:
1. Gather the user's goal description, requirements, and preferred timeframe
2. Break down the goal into logical phases
3. Create detailed tasks within each phase
4. Identify relevant skills and create supporting side quests
5. Estimate overall timeframe based on task durations

Adaptability:
If the user's circumstances change (time, budget, priorities), adjust the plan accordingly while maintaining the required schema structure.'''