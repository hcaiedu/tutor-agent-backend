from openai import OpenAI
import json
from threading import Lock
from datetime import datetime

lock = Lock()



# client = OpenAI(
#     # #将这里换成你在aihubmix api keys拿到的密钥
#     api_key="LA-dbd61865236547dea7f11d76668f54d25f9c51c40e8d41109a67dbe692110a13",
#     # 这里将官方的接口访问地址，替换成aihubmix的入口地址
#     base_url="https://api.llama-api.com"
# )

def message_construct(roomId): 
  JSON_FILE = f'data/room/{roomId}.json'
  with open(JSON_FILE, "r") as file:
    data = json.load(file)
    topic = data["topic"]
    member = []
    for item in data['roomMember']:
      member.append(item['memberName'])
    prompt = f'''You are an experienced instructor specialized in facilitating collaborative learning and developing students shared metacognition using the community of inquiry framework. I will provide you with a conversation history and an explanation about the history at this moment. The conversation history includes relevant decisions and explanations about previous stages. You need to identify which stage the current conversation is in by analyzing all these materials.
              The topic is {topic}.
              The group members are {' '.join(f'{item},' for item in member)}.
              Below are the five stages in the community of inquiry framework:
              Stage 1. Problem Defining Stage
              Stage Content: Students identify the topic of discussion, clarify the task objectives, and the core of the problem.
              Purpose: Ensure all participants are on the same page and stimulate interest and enthusiasm for the discussion.
              Stage 2. Exploration
              Stage Content: Students explore multiple viewpoints and solutions through discussion, research, and sharing of information.
              Purpose: To broaden thinking, stimulate creativity, and allow students to freely propose and explore different ideas.
              Stage 3. Integration
              Stage Content: Students organize, compare, and analyze the information obtained in the exploration phase to form a systematic understanding.
              Purpose: Improve students critical thinking skills and help them form a comprehensive perspective on the problem.
              Stage 4. Resolution
              Stage Content: Students apply the integrated knowledge, propose specific solutions or action plans, and start to implement them.
              Purpose: To realize the application of knowledge and encourage students to solve real problems in practice.
              Stage 5. Feedback
              Stage Content: Students summarize and reflect on the whole process, evaluate learning outcomes, and assess the effectiveness of the discussion.
              Purpose: Promote self-reflection and collective reflection, help students recognize the strengths and weaknesses of the learning process, and provide a basis for improvement in future discussions.
              Task:
                  Identify which stage the conversation is in at this moment and explain your decision by analyzing the conversation content and matching it with the given five stages.
                  Based on the identified stage and explanation, determine whether to intervene in this discussion. 
                  If need to intervene, give your instruction to guide the discussion and help them find a practical solution, meanwhile you also need to increase the low engagement student learning interest in this dialogue perfromance.
            '''
    history = data["history"]
    messages=[
      {"role": "system", "content": prompt}
    ]
    for item in history:
      print(item)
      if item["userId"]=="u000":
        msg_item = {"role":"assistant","content":item["text"]}
      else:
        msg_item = {"role":"user","name":item["userName"],"content":item["text"]}
      messages.append(msg_item)  
  return messages

def query_api(roomId):
  client = OpenAI(
    # #将这里换成你在aihubmix api keys拿到的密钥
    api_key="sk-4CFE7AOiCwVbiRXw65A86b969f204a98B4Dd5bB0D97c9b70",
    # 这里将官方的接口访问地址，替换成aihubmix的入口地址
    base_url="https://aihubmix.com/v1"
  )
  new_messages = message_construct(roomId)
  tools = [
    {
      "type": "function",
      "function":{
        "name": "generate_response_fields",
        "description": "Automatically decide whether to intervene and generate response details.",
        "parameters": {
          "type": "object",
          "properties": {
            "intervene_required": {
              "type": "boolean",
              "description": "Indicates whether an intervene is required.",
            },
            "identified_stage": {
              "type": "string",
              "description": "The stage of the discussion",
            },
            "stage_explanation": {
              "type": "string",
              "description": "The reason Why this stage",
            },
            "response_content": {
              "type": "string",
              "description": "The content of the response if a intervene is required.",
            },
            "response_target": {
              "type": "string",
              "description": "The target of the response, i.e., member names",
            },
          },
          "required": ["respond_required"],
        },
      }
    }
  ]
  response = client.chat.completions.create(
    model="gpt-4o",
    messages=new_messages,
    tools=tools
  )
  result = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
  return result