from concurrent.futures import thread
from email.mime import image
import os
from pydoc import cli
import re
from openai import OpenAI, AzureOpenAI
from flask import Flask, render_template, request, jsonify
import json
import requests
import mysql.connector
from secrets2 import get_keys
import time

db_pwd="KichuAchu123!"
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


@app.route("/get_sql_response", methods=['GET', 'POST'])
def get_sql_response():
    if request.method == 'POST':
        #message = request
        message = request.data.decode('utf-8')
    else:  # This handles the GET request case
        message = request.args.get("message")

    message=json.loads(message)
    
    mycursor = mydb.cursor()
    mycursor.execute("use test_db;")
    mycursor.execute(message['message'])
    
    x = [i for i in mycursor]

    #UNCOMMENT THESE LINES TO VIEW THE SQL QUERY AND THE RESPONSE RETURNED
    print(message['message'])
    print(x)
    y = [list(i) for i in x][0:]
    y = "  \n".join([str(i) for i in y])
    print(y)

    return " ".join(x)
    # msg_mood = [{
    #     "role":"system",
    #     "content":"Give an answer to the prompt in a sentence."
    # },
    # {
    #     "role":"user",
    #     "content":message['message'] + "\n  " + y
    # }]


    # response_mood = client.chat.completions.create(
    #     model=model,
    #     messages=msg_mood,
    #     temperature=0.7,
    #     max_tokens=64,
    #     top_p=1
    # )

    # #creating the assistant and using code interpreter

    # image_path = "./charts/chart"
    # s = image_path
    # count = 0
    # while True:
    #     if os.path.exists(s + '.png'):
    #         count+=1
    #         s += count
    #     else:
    #         break
    # image_path = s + '.png'
    
    # chart_prompt = "Please generate a chart using following data: \n" + y
    
    # thread = client.beta.threads.create(
    #             messages=[
    #                 {
    #                     "role": "user",
    #                     "content": chart_prompt,
    #                 }
    #             ]
    #         )

    # run = client.beta.threads.runs.create(
    #             assistant_id="asst_SKv2djMWyDKQgM7yASe3S88g", 
    #             thread_id=thread.id)

    # while True:
    #     run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
    #     if run.status == "completed":
    #         messages = client.beta.threads.messages.list(thread_id=thread.id)

    #         image_file_id = messages.data[0].content[0].image_file.file_id
    #         content_description = messages.data[0].content[1].text.value

    #         print(image_file_id)
    #         raw_response = client.files.with_raw_response.content(file_id=image_file_id)

    #         client.files.delete(image_file_id)
    #         with open(image_path, "wb") as f:
    #             f.write(raw_response.content)
    #             return (content_description)

    #     elif run.status == "failed":
    #         print("Sorry, something went wrong. Please try again.")
    #         break

    #     time.sleep(1)





    # response_content_mood = response_mood.choices[0].message.content
    
    # return response_content_mood


if __name__ == "__main__":
    app.run(debug=True)