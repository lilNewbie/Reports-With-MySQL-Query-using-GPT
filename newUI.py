import email
from urllib import response
import streamlit as st
import random 
import time
import json
import openai
from openai import OpenAI
import requests
from mailjet_rest import Client
from secrets2 import get_keys

# st.sidebar.header('Required API Keys')

# Add input widgets to the sidebar for three strings
# mailjet_api_key = st.sidebar.text_input("Enter MailJet API's public key", '', type='password')
# mailjet_api_secret = st.sidebar.text_input("Enter MailJet API's private key", '', type='password')
# openai_secret_key = st.sidebar.text_input("Enter OpenAI's API key", '', type='password')

#st.sidebar.markdown('Sample Prompt')
#st.sidebar.markdown('"Send an email from x to y with the subject as test and content of the email explaining the same"')

#Send an email from alan.learning.acc@gmail.com to alan.learning.acc2@gmail.com with the Subject as "The Fall of Rome" and the Content explaining it in two sentences. Sign off as "The Emperor".

#mailjet_api_key = st.secrets['MAILJET_API_KEY']
#mailjet_api_secret = st.secrets['MAILJET_API_SECRET']

openai_secret_key, mailjet_api_key, mailjet_api_secret, db_pwd = get_keys()


st.title("GPT_Mail")
# st.markdown("Can be used only after the API Keys have been entered")

mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret))
client = OpenAI(api_key=openai_secret_key)
GPT_MODEL = 'gpt-3.5-turbo-0613'


def create_run_and_thread(messages):
    prompt = messages
    thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Use the following table - \n  \n  create table mood_freq_table(\n  sno int not null,\n  name varchar(20),\n  mood varchar(15),\n  frequency int,\n  primary key (sno)\n  );" + prompt,
                    }
                ]
            )

    run = client.beta.threads.runs.create(
                assistant_id="asst_fungujY0Z2a2jk2Puoq5DCVo", 
                thread_id=thread.id,
                instructions=""
                )
    return run, thread

# def check_poll(run,thread):
    # while True:
        # run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
        # if run.status == "completed":
        #     messages = client.beta.threads.messages.list(thread_id=thread.id)
        #     print(messages)
        #     # image_file_id = messages.data[0].content[0].image_file.file_id
        #     content_description = messages.data[0].content[0].text.value
        #     message_placeholder.markdown(content_description)
        #     # print(image_file_id)
        #     # raw_response = client.files.with_raw_response.content(file_id=image_file_id)

        #     # client.files.delete(image_file_id)
        #     # with open(content_description, "wb") as f:
        #     #     f.write(raw_response.content)
        #     #     print(content_description)
def check_poll(run,thread):
    while True:
        run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
        if run.status == "requires_action":
            return run

        elif run.status == "failed":
            print("Sorry, something went wrong. Please try again.")
            return -1

        time.sleep(2)



# def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer " + st.secrets['OPENAI_API_KEY'],
#     }
#     json_data = {"model": model, "messages": messages}
#     if tools is not None:
#         json_data.update({"tools": tools})
#     if tool_choice is not None:
#         json_data.update({"tool_choice": tool_choice})
#     try:
#         response = requests.post(
#             "https://api.openai.com/v1/chat/completions",
#             headers=headers,
#             json=json_data,
#         )
#         return response
#     except Exception as e:
#         print("Unable to generate ChatCompletion response")
#         print(f"Exception: {e}")
#         return e

def send_sql_query(sql_query):
    json_data = {"message": sql_query}
    try:
        response = requests.post(
            "http://localhost:5000/get_sql_response",
            json=json_data,
        )
        print(response.text)
        return response.text
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to the specified email with the subject, content and attached files",
            "parameters":{
                "type": "object",
                "properties": {
                    "FromEmail": {
                        "type": "string",
                        "description": "The email address, eg., alan.learning.acc@gmail.com"
                    },
                    "FromName": {
                        "type": "string",
                        "description": "The name of the sender, eg., Aloo"
                    },
                    "Subject": {
                        "type": "string",
                        "description": "Subject of the email"
                    },
                    "Text-part": {
                        "type": "string",
                        "description": "The content of the email"
                    },
                    "Recipients": {
                        "type": "string",
                        "description": "The recipients' email addresses"
                    },
                    "Attachments": {
                        "type":"object",
                        "description":"A list containing dictionaries for each image. Each dictionary has 'Content-type', 'Filename' and 'content' as the keys. 'Content-type' takes the value 'image/png', 'Filename' takes the name of the file and 'content' takes the Base64 encoded form of the image. "
                    }
                },
                "required": ["FromEmail", "FromName", "Subject", "Text-part", "Recipients","Attachments"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_sql_query",
            "description": "Send a sql query to get the required data from a table with the following schema - \n  \n  create table mood_freq_table(\n  sno int not null,\n  name varchar(20),\n  mood varchar(15),\n  frequency int,\n  primary key (sno)\n  );",
            "parameters":{
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The sql query alone as a string"
                    }
                },
                "required": ["sql_query"]
            }
        }
    }
]

def get_function_called(prompt):
    run, thread = create_run_and_thread(prompt)
    run = check_poll(run, thread)
    if run!=-1:
        required_actions = run.required_action.submit_tool_outputs
        with open('/jsons/required_actions.json','w') as f:
            required_actions_json = required_actions.model_dump()
            json.dump(required_actions_json,f,indent=4)
    tool_ops = []

    for action in required_actions.tool_calls:
        func_name = action.function.name
        arguments = json.loads(action.function.arguments)
        if func_name=="send_sql_query":
            op = send_sql_query(arguments['sql_query'])



# def converter(em):
#     em_dict = {}
#     names = ['FromEmail','FromName','Subject','Text-part','Recipients']
#     for i in range(0,len(em)-1):
#         s = em[i].split(':')
#         key = names[i]
#         value = s[1][2:-2]
#         em_dict[key] = value

#     s = em[len(em)-1].split(':')
#     key = names[len(em)-1]
#     value = s[1][2:-1]
#     em_dict[key] = [{'Email':value}]
#     return em_dict

#code to load previous messages if any
if 'openai_model' not in st.session_state:
    st.session_state['openai_model']="gpt-3.5-turbo"

if 'messages' not in st.session_state:
    st.session_state.messages=[]


for message in st.session_state.messages:
    with st.chat_message(message['role']):
        # cont = message['content']
        # if message['role']=="assistant":
            # cont = 'Email has been sent from '+ cont['FromEmail'] + ' to ' + cont['Recipients'][0]['Email']  + '  \n' + 'Check inbox.  \n' + 'Content sent:  \n'+ cont['Text-part']
        st.markdown(message['content'])


if prompt := st.chat_input('Type in the data required'):
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    em = ""      
    with st.chat_message('assistant'):
        message_placeholder = st.empty()
        #full_response = sql_query_request(prompt)
        full_response = get_function_called(prompt)
        # email_format = full_response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments']

        # em = email_format.split('\n')
        # em = em[1:-1]
        # em = converter(em)

        # result = mailjet.send.create(data=em)
        
        
        # cont = 'Email has been sent from '+ em['FromEmail'] + ' to ' + em['Recipients'][0]['Email']  + '  \n' + 'Check inbox.  \n' + 'Content sent:  \n'+ em['Text-part']
        
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({'role':'assistant','content':em})
