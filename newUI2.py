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
import utils

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

mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret))
client = OpenAI(api_key=openai_secret_key)
GPT_MODEL = 'gpt-3.5-turbo-0613'

if 'openai_model' not in st.session_state:
    st.session_state['openai_model']="gpt-3.5-turbo"

if 'messages' not in st.session_state:
    st.session_state.messages=[]


for message in st.session_state.messages:
    with st.chat_message(message['role']):st.markdown(message['content'])


if prompt := st.chat_input('Type in the data required'):
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    em = ""      
    with st.chat_message('assistant'):
        message_placeholder = st.empty()
        #full_response = sql_query_request(prompt)
        full_response = utils.get_function_called(prompt)
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({'role':'assistant','content':em})
