import time
import json
from openai import OpenAI
import requests
from mailjet_rest import Client
from secrets2 import get_keys
from PIL import Image
import io
import os
import pybase64
from mailjet_rest import Client
import streamlit as st

openai_secret_key, MAILJET_API_KEY, MAILJET_API_SECRET, db_pwd = get_keys()
client = OpenAI(api_key=openai_secret_key)
mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET))


tools = [{
    "type":"function",
    "function":{
        "name": "send_sql_query",
        "description": "Send a sql query to get the required data from a table with the following schema - \n  \n  create table mood_freq_table(\n  sno int not null,\n  name varchar(20),\n  mood varchar(15),\n  frequency int,\n  primary key (sno)\n  );",
        "parameters": {
            "type": "object",
            "properties": {
            "sql_query": {
                "type": "string",
                "description": "The sql query alone as a string"
            }
            },
            "required": [
            "sql_query"
            ]
        }
    }
},
{
    "type":"function",
    "function":{
        "name": "send_email",
        "description": "Send an email to the specified email with the subject, content and attached files",
        "parameters": {
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
                "type": "object",
                "description": "A list containing dictionaries for each image. Each dictionary has 'Content-type', 'Filename' and 'content' as the keys. 'Content-type' takes the value 'image/png', 'Filename' takes the name of the file and 'content' takes the Base64 encoded form of the image. "
            }
            },
            "required": [
            "FromEmail",
            "FromName",
            "Subject",
            "Text-part",
            "Recipients",
            "Attachments"
            ]
        }
    }
},
{"type":"retrieval"},
{"type":"code_interpreter"}]



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
        print("Unable to generate response")
        print(f"Exception: {e}")
        return e

def send_email(prompt):
    print(prompt.keys())
    res = mailjet.send.create(data=prompt)
    return('Email has been sent')

def create_assistant():
    assistant_id_file = 'assistant_id.txt'
    if os.path.exists(assistant_id_file):
        with open(assistant_id_file, 'r') as file:
            assistant_id = file.read().strip()
    else:
        assistant = client.beta.assistants.create(
            name="Data Plotter",
            instructions="You are a data visualizer. Your role is to call functions to generate sql queries for the given schema - '\n  \n  create table mood_freq_table(\n  sno int not null,\n  name varchar(20),\n  mood varchar(15),\n  frequency int,\n  primary key (sno)\n  ); ' and to retrieve data from it and plot graphs and charts and save the images as png files.  You can send an email containing the images only if requested by the user.",
            model='gpt-3.5-turbo-1106',
            tools=tools
        )
        assistant_id = assistant.id
        with open(assistant_id_file, 'w') as file:
            file.write(assistant_id)
    assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
    print(f'Assistant with id {assistant_id} retrieved.')

    return assistant



def create_thread():
    print("Creating a thread for new convo")
    thread = client.beta.threads.create()
    print(f'Thread created. ID - {thread.id}')
    return thread

def send_message_and_run_assistant(thread, assistant, user_message):
    print('User message added to thread: '+user_message)
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=user_message
    )
    print('Running the assistant')
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    return run

def poll_run_status(thread, run):
    while True:
        run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
        if run.status in ['completed','failed','cancelled']:
            break
        elif run.status == 'requires_action':
            prompt, if_send_email = handle_required_actions(thread, run)
        else:
            print('waiting')
            time.sleep(3)
    return run, prompt, if_send_email

def handle_required_actions(thread, run):
    print('Assistant req function calls')
    required_actions = run.required_action.submit_tool_outputs
    with open('jsons/required_actions.json','w') as f:
            required_actions_json = required_actions.model_dump()
            json.dump(required_actions_json,f,indent=4)
    tool_outputs = []

    prompt = ""
    if_send_email = False

    for action in required_actions.tool_calls:
        func_name = action.function.name
        arguments = json.loads(action.function.arguments)
        if func_name=="send_sql_query":
            output = send_sql_query(arguments['sql_query'])
        elif func_name=="send_email":
            prompt = arguments
            if_send_email = True
            output = 'Email sent'
        else:
            raise ValueError(f'Unkown function {func_name}')
        print(f'{func_name} has been called with arguments: {arguments}')
        tool_outputs.append({
            'tool_call_id':action.id,
            'run_id':run.id,
            'output':output
        })
    print('Submitting fn call back to Assistant')
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )
    return prompt, if_send_email


def load_imgs(path):
    files = os.listdir(path)
    file_list = {}
    for i in files:
        with open(f"charts/{i}", "rb") as img_file:
            file_list[i] = pybase64.b64encode(img_file.read()).decode('utf-8')
    return file_list



def display_final_response(thread,run,prompt,if_send_email):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id,run_id=run.id)

    with open('jsons/run_steps.json','w') as f:
        run_steps_json = run_steps.model_dump()
        json.dump(run_steps_json,f,indent=4)

    with open('jsons/messages.json','w') as f:
        messages_json = messages.model_dump()
        json.dump(messages_json,f,indent=4)
    op_string = ""
    for msg in messages.data:
        for content in msg.content:
            if hasattr(content, 'image_file'):
                continue
            if hasattr(content, 'text'):        
                op_string = f"{msg.role.capitalize()}: {content.text.value}"
                print(op_string)

    updated_messages = []

    #images
    image_counter = 0
    for message in messages.data:
        if message.content:
            citations = []
            for content_part in message.content:
                if content_part.type == 'text':
                    annotations = content_part.text.annotations
                    text_value = content_part.text.value
                    op_string = text_value
                    if annotations!=[]:
                        for index, annotation in enumerate(annotations):
                            text_value = text_value.replace(annotation.text, f' [{index}]')
                            if (file_citation := getattr(annotation, 'file_citation',None)):
                                cited_file = client.files.retrieve(file_citation.file_id)
                                citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')

                            elif (file_path := getattr(annotation, 'file_path',None)):
                                cited_file = client.files.retrieve(file_path.file_id)
                                image_file_id = cited_file.id
                                image_data : bytes = client.files.with_raw_response.content(image_file_id).content
                                image = Image.open(io.BytesIO(image_data))
                                image.save(f'charts/chart{image_counter}.png')
                                image_counter += 1
                
                elif content_part.type == 'image_file':
                    image_file_id = content_part.image_file.file_id
                    image_data : bytes = client.files.with_raw_response.content(image_file_id).content
                    image = Image.open(io.BytesIO(image_data))
                    image.save(f'charts/chart{image_counter}.png')
                    image_counter += 1

            updated_messages.append(message)
    op_string = 'The graph'
    if if_send_email:
        imgs = load_imgs('charts')
        prompt['Attachments'] = []
        prompt['Recipients'] = [{"Email":prompt['Recipients']}]
        for i in imgs.keys():
            img_dict = {
                'Content_type':'image/png',
                'Filename':i,
                'content':imgs[i]
            }
            prompt['Attachments'].append(img_dict)
        # print(send_email(prompt))
        op_string = send_email(prompt)
        image_counter = -1
    return op_string, image_counter


if 'messages' not in st.session_state:
    st.session_state.messages=[]


for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message['role']=='assistant':
            if message['image']!=-1:
                st.image(message['image'],'')



thread = create_thread()
assistant = create_assistant()
if user_message := st.chat_input('Type in the data required'):
    with st.chat_message('user'):
        st.markdown(user_message)
    st.session_state.messages.append({'role':'user','content':user_message})
    
    img = -1
    with st.chat_message('assistant'):
        message_placeholder = st.empty()
        run = send_message_and_run_assistant(thread,assistant,user_message)
        run, prompt, if_send_email = poll_run_status(thread,run)

        resp, img = display_final_response(thread,run,prompt,if_send_email)
        message_placeholder.markdown(resp)
    st.session_state.messages.append({'role':'assistant',
                                    'content':resp,
                                    'image':f'charts/chart{img-1}.png' if img!=-1 else ''})

    # Plot the graphs for the total frequencies of all the moods and save the image






