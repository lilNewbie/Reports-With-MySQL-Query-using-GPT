
# Reports With MySQL Query using GPT

This repository contains the files used to create this custom GPT which allows users to send emails to recipient emails with the subject and content generated by the GPT model.


## Features

- Chatbot-like interface using Streamlit
- Uses the Assistants API of OpenAI's GPT-3.5 Turbo model
- Uses the MailJet API to enable email delivery



## Run Locally

Clone the project

```bash
https://github.com/lilNewbie/Reports-With-MySQL-Query-using-GPT.git
```

Go to the project directory

```bash
  cd Reports-With-MySQL-Query-using-GPT
```

Install dependencies

```bash
  pip install -r requirements.txt
```

The get_keys() function returns the keys from a secrets2.py file
```python
from secrets2 import get_keys
openai_secret_key, mailjet_api_key, mailjet_api_secret, db_pwd = get_keys()
```

I have added functionality to add keys to a sidebar widget before interacting with the ChatBot.

```python
st.sidebar.header('Required API Keys')

#Add input widgets to the sidebar for three strings
mailjet_api_key = st.sidebar.text_input("Enter MailJet API's public key", '', type='password')
mailjet_api_secret = st.sidebar.text_input("Enter MailJet API's private key", '', type='password')
openai_secret_key = st.sidebar.text_input("Enter OpenAI's API key", '', type='password')
```

Run the web-app

```bash
  streamlit run func.py
```


## Usage/Examples


