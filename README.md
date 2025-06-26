# Project Title
**Tutor Agent Backend** by ***EDUHK LTTC Human Centric AI Group***

## Prerequisites
Requirements for **Python**, **MongoDB**
## Install
```sh
pip install -r requirements.txt
```

## Run
```sh
python app.py
```

## Project Structure
```
tutor-agent-backend
├─ agent_utils.py //functions for prompt construction, agent construction
├─ app.py //main python file, the system entry, functions for APIs and chat message broadcast
├─ database.py //the database connection
├─ excel.ipynb //use this file to generate mongodb database documents
├─ multi_agent_interaction_testing.xlsx //predefined groups and users, you can use this file to generate databse documents
├─ ollama_api_test.ipynb //test local ollama api
├─ Polyu_api_test.ipynb //test polyu llm api
├─ prompts //prompts file
│  ├─ student_prompt.docx
│  └─ teacher_prompts
│     ├─ intervention prompt.docx
│     ├─ issue_prompts
│     │  ├─ stage1.docx
│     │  ├─ stage2.docx
│     │  ├─ stage3.docx
│     │  ├─ stage4.docx
│     │  └─ stage5.docx
│     └─ stage_prompt.docx
├─ prompt_utils.py //some tool functions for prompt generation
└─ README.md
```