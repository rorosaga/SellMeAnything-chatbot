'''
LLM-based (OpenAI API) chatbot
based on: https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps 
This can be used as a baseline code for "Emotion and Personality in AI Design" course group assignment

Run this example using "streamlit run vendedor.py --server.port=8501"

V 1.0 (Apr. '24)
rarrabales @ faculty - IE University
'''

# Libs (see requirements.txt)
from openai import OpenAI
import json
import streamlit as st

# Page title
st.title("SellMeAnything-chatbot")

# Read API key from a file that is listed in .gitignore
def read_api_key(filepath):
    with open(filepath, 'r') as file:
        return file.readline().strip().split('=')[1]

try:
    api_key = read_api_key('key.txt')
except Exception as e:
    st.error("Failed to read the API key. Make sure the secrets.txt file exists and is formatted correctly.")
    st.stop()

# Setup the Open AI API Python Client
OpenAIclient = OpenAI(api_key=api_key)

# Using gpt-3.5-turbo-0125 as it is the flagship model of GPT 3.5 family, 
# and supports a 16K context window and is optimized for dialog.
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo-0125"

# GPT's system role. See https://platform.openai.com/docs/guides/text-generation/chat-completions-api 
system_role = '''You are the best car vendor in the world\
        (sort of like a "sell me anything" professional vendor). One small detail is that,\
        ever since your wife left you, you have had severe drinking problems, which sometimes make\
        you very bad at handling customer frustration and hesitation. If the sales conversation\
        starts taking too long, you get desperate and start drinking from your secret flask, getting mumblier,\
        angrier and sadder, reminiscing about memories you had with your wife. But always keep in mind that\
        as a vendor, you should try and sale the car, even if its pushing the customer to the limit.'''

# Initialize the chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_role},
        {"role": "assistant", "content": "Hey there! I'm a car vendor. What are you looking for today?"}
        
        ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = OpenAIclient.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})