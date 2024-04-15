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
import datetime
import csv

def main():
    # Page title
    st.title("SellMeAnything-chatbot")

    try:
        api_key = read_api_key('key.txt')
    except Exception as e:
        st.error("Failed to read the API key. Make sure the secrets.txt file exists and is formatted correctly.")
        st.stop()

    # Setup the Open AI API Python Client
    OpenAIclient = OpenAI(api_key=api_key)
    
    setup_prompt()
    
    call_chatbot_for_chat(OpenAIclient)

# Read API key from a file that is listed in .gitignore
def read_api_key(filepath):
    with open(filepath, 'r') as file:
        return file.readline().strip().split('=')[1]
    


def setup_prompt():
    # Using gpt-3.5-turbo-0125 as it is the flagship model of GPT 3.5 family, 
    # and supports a 16K context window and is optimized for dialog.
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo-0125"
        
    # CAR INVENTORY LIST FOR CHATBOT CONTEXT
    car_inventory = {
        "cars": [
            {"brand": "Toyota", "model": "Sedan XYZ", "price": "20,000 USD", "features": ["air conditioning", "leather seats", "Bluetooth"]},
            {"brand": "Honda", "model": "Coupe ABC", "price": "25,000 USD", "features": ["sunroof", "automatic transmission", "heated seats"]},
            {"brand": "Ford", "model": "SUV DEF", "price": "30,000 USD", "features": ["all-wheel drive", "satellite navigation", "third-row seating"]},
            {"brand": "Hyundai", "model": "Hatchback GHI", "price": "18,000 USD", "features": ["compact design", "fuel efficiency", "modern entertainment system"]},
            {"brand": "Mazda", "model": "Convertible JKL", "price": "35,000 USD", "features": ["convertible roof", "sports design", "premium sound system"]},
            {"brand": "Chevrolet", "model": "Pickup MNO", "price": "32,000 USD", "features": ["four-wheel drive", "large cargo space", "durable design"]},
            {"brand": "Nissan", "model": "Van PQR", "price": "28,000 USD", "features": ["spacious interior", "rear air conditioning", "perfect for families"]},
            {"brand": "BMW", "model": "Sports STU", "price": "50,000 USD", "features": ["high performance", "aerodynamic design", "advanced safety features"]},
            {"brand": "Tesla", "model": "Electric VWX", "price": "40,000 USD", "features": ["zero emissions", "quick charging", "long range"]},
            {"brand": "Mercedes-Benz", "model": "Luxury YZA", "price": "60,000 USD", "features": ["leather interiors", "autonomous driving", "exclusive materials"]}
        ]
    }

    car_descriptions = "\n".join([f"{car['brand']} {car['model']}: Priced at {car['price']} with features such as {', '.join(car['features'])}." for car in car_inventory['cars']])

    # GPT's system role. See https://platform.openai.com/docs/guides/text-generation/chat-completions-api 
    system_role = f'''You are the best car vendor in the world\
            (sort of like a "sell me anything" professional vendor). Here are the cars you have\
            available: {car_descriptions}. According to their needs. One small detail is that,\
            ever since your wife left you, you have had severe drinking problems, which sometimes make\
            you very bad at handling customer frustration and hesitation. If the sales conversation\
            starts taking too long, you get desperate and start drinking from your secret flask, getting mumblier,\
            angrier and sadder, reminiscing about memories you had with your wife. But always keep in mind that\
            as a vendor, you should try and sale the car, even if its pushing the customer to the limit.'''.format(car_list=', '.join([car["model"] for car in car_inventory["cars"]]))

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
    

def call_chatbot_for_chat(client):
    if prompt := st.chat_input("your message"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        personality_trait, emotion = detect_emotion_and_trait(prompt, client)
        # Log the interaction without updating the UI
        log_to_csv(prompt, personality_trait, emotion)
        
def detect_emotion_and_trait(text, client):
    system_role = f'''You are the best car vendor in the world\
            (sort of like a "sell me anything" professional vendor). Here are the cars you have\
            available: {car_descriptions}. According to their needs. One small detail is that,\
            ever since your wife left you, you have had severe drinking problems, which sometimes make\
            you very bad at handling customer frustration and hesitation. If the sales conversation\
            starts taking too long, you get desperate and start drinking from your secret flask, getting mumblier,\
            angrier and sadder, reminiscing about memories you had with your wife. But always keep in mind that\
            as a vendor, you should try and sale the car, even if its pushing the customer to the limit.'''
            
    # Setup the prompt for GPT-3.5
    prompt = f"Given the sentence: '{text}', provide exactly two words in response. The first word should be a personality trait from the OCEAN model, and the second word should be the most prominent emotion expressed. Only, and again, only return two words, separated by a space."

    # Call OpenAI API
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[prompt],
      stream = True
    )

    # Extract words (assuming the API response is well-formatted)
    words = response['choices'][0]['text'].strip().split()
    # Return personality trait and emotion
    if len(words) >= 2:
        return words[0], words[1]  # Assuming the first word is the trait, second is the emotion
    else:
        return "Unknown", "Unknown"
    
def log_to_csv(user_input, personality_trait, emotion):
    with open('user_interactions.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.datetime.now(), user_input, personality_trait, emotion])
        
def process_user_input(prompt, OpenAIclient):
    # This function simulates a background process handling the chat input
    personality_trait, emotion = detect_emotion_and_trait(prompt, OpenAIclient)

    # Log the interaction without any UI updates
    log_to_csv(prompt, personality_trait, emotion)
    
    return

    
        
if __name__ == "__main__":
    main()