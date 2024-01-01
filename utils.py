import email
from urllib import response
import time
import json
from openai import OpenAI
import requests
from mailjet_rest import Client
from secrets2 import get_keys
from PIL import Image
import io

openai_secret_key, MAILJET_API_KEY, MAILJET_API_SECRET, db_pwd = get_keys()
client = OpenAI(api_key=openai_secret_key)

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
    
def send_email(prompt):
    print(prompt)
    return('Email has been sent')

def create_thread():
    print("Creating a thread for new convo")
    thread = client.beta.threads.messages.create()
    print(f'Thread created. ID - {thread.id}')
    return thread

def send_message_and_run_assistant(thread, user_message):
    print('User message added tp thread: '+user_message)
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        assistant_id='asst_eujY4eWEatR82O1aPaw3tzZ5'
    )
    print('Running the assistant')
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='asst_eujY4eWEatR82O1aPaw3tzZ5'
    )
    return run

def poll_run_status(thread, run):
    while True:
        run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
        if run.status in ['completed','failed','cancelled']:
            break
        elif run.status == 'requires_action':
            handle_required_actions(thread, run)
        else:
            print('waiting')
            time.sleep(3)
    return run

def handle_required_actions(thread, run):
    print('Assistant req function calls')
    required_actions = run.required_action.submit_tool_outputs
    with open('/jsons/required_actions.json','w') as f:
            required_actions_json = required_actions.model_dump()
            json.dump(required_actions_json,f,indent=4)
    tool_outputs = []

    for action in required_actions.tool_calls:
        func_name = action.function.name
        arguments = json.loads(action.function.arguments)
        if func_name=="send_sql_query":
            output = send_sql_query(arguments['sql_query'])
        elif func_name=="send_email":
            prompt = arguments
            output = send_email(prompt)
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

def display_final_response(thread,run):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id,run_id=run.id)

    with open('/jsons/run_steps.json','w') as f:
        run_steps_json = run_steps.model_dump()
        json.dump(run_steps_json,f,indent=4)

    with open('/jsons/messages.json','w') as f:
        messages_json = messages.model_dump()
        json.dump(messages_json,f,indent=4)

    for msg in messages.data:
        for content in msg.content:
            if hasattr(content, 'image_file'):
                continue
            if hasattr(content, 'text'):
                print(f"{msg.role.capitalize()}: {content.text.value}")

    updated_messages = []

    #images
    image_counter = 0
    for message in messages.data:
        if message.content:
            citations = []
            for content_part in message.content:
                if content_part.type == 'text':
                    annotations = content_part.text.value
                    text_value = content_part.text.value
                    for index, annotation in enumerate(annotations):
                        text_value = text_value.replace(annotation.text, f' [{index}]')
                        if (file_path := getattr(annotation, 'file_path',None)):
                            cited_file = client.files.retrieve(file_path.file_id)
                            image_file_id = cited_file.id
                            image_data : bytes = client.files.with_raw_response.content(image_file_id).content
                            image = Image.open(io.BytesIO(image_data))
                            image.save(f'chart{image_counter}.png')
                            image_counter += 1
                
                elif content_part.text.value == 'image_file':
                    image_file_id = content_part.image_file.file_id
                    image_data : bytes = client.files.with_raw_response.content(image_file_id).content
                    image = Image.open(io.BytesIO(image_data))
                    image.save(f'chart{image_counter}.png')
                    image_counter += 1

            updated_messages.append(message)
    return updated_messages
    
if __name__=="__main__":
    thread = create_thread()
    while True:
        user_message = input('Message pls: ')
        if user_message.lower == 'quit':
            break
        
        run = send_message_and_run_assistant(thread,user_message)
        run = poll_run_status(thread,run)

        resp = display_final_response(thread,run)






