import os
from pydoc import cli
import re
import openai
from openai import OpenAI, AzureOpenAI
from flask import Flask, render_template, request, jsonify
import json
import requests
import mysql.connector
from secrets2 import get_keys

# load env vars from .env file
openai_api_key, azure_api_key, azure_api_version, db_pwd, azure_ep = get_keys()
model = 'gpt-3.5-turbo-1106'

client = OpenAI(api_key=openai_api_key)

client2 = AzureOpenAI(
    azure_endpoint=azure_ep,
    api_key=azure_api_key,
    api_version=azure_api_version
    )

#load my database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=db_pwd
)

app = Flask(__name__)

def database_call(query):
    return query

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_response", methods=['GET', 'POST'])
def get_response():
    if request.method == 'POST':
        #message = request
        message = request.data.decode('utf-8')
    else:  # This handles the GET request case
        message = request.args.get("message")

    message=json.loads(message)
    msg_query = [{ "role": "system","content": "Given the following SQL tables, your job is to write queries given a users request.\n  \n  create table mood_freq_table(\n  sno int not null,\n  name varchar(20),\n  mood varchar(15),\n  frequency int,\n  primary key (sno)\n  );"}]
    msg_query.append({"role":"user","content":message['message']})

    response="hehe"
    response = client.chat.completions.create(
        model=model,
        messages=msg_query,
        temperature=0.7, 
        max_tokens=64,
        top_p=1
    )
    
    response_content = response.choices[0].message.content
    
    mycursor = mydb.cursor()
    mycursor.execute("use test_db;")
    mycursor.execute(response_content.split("```sql")[1][:-3])
    
    x = [i for i in mycursor]

    

    #UNCOMMENT THESE LINES TO VIEW THE SQL QUERY AND THE RESPONSE RETURNED
    print(response_content.split("```sql")[1][:-3])
    print(x)
    y = [list(i) for i in x][0:]
    y = "  \n".join([str(i) for i in y])
    print(y)
    msg_mood = [{
        "role":"system",
        "content":"Give an answer to the prompt in a sentence."
    },
    {
        "role":"user",
        "content":message['message'] + "\n  " + y
    }]


    response_mood = client.chat.completions.create(
        model=model,
        messages=msg_mood,
        temperature=0.7,
        max_tokens=64,
        top_p=1
    )

    #creating the files obj
    file1 = client.files.create(
        file=open('generate.txt','rb'),
        purpose='assistants'
    )
    

    #creating the assistant and using code interpreter
    assistant_graph = client.beta.assistants.create(
        name="Data visualizer",
        instructions="You must generate a relevant bar graph using the inputs",
        model=model,
        tools=[{"type":"code_interpreter"}]
    )

    assistant_file = client.beta.assistants.files.create(
        assistant_id=assistant_graph.id,
        file_id=file1.id
    )


    thread = client.beta.threads.create(
        messages=[{
            "role":"user",
            "content":"Create graphs and store them in images for the given inputs  \n",
        }]
    )

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="I want to see a bar graph generated using the following information.  \n" + y
    )


    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_graph.id,
        instructions="You must generate a relevant bar graph using the inputs"
    )

    returned_msg = client.beta.threads.messages.retrieve(
            thread_id=thread.id,
            message_id=message.id
        )

    print(returned_msg)

    response_content_mood = response_mood.choices[0].message.content

    return response_content_mood

if __name__ == "__main__":
    app.run(debug=True)