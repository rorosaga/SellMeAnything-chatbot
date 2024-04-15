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
    st.title("Your Personal Ferrari Car Vendor")

    try:
        api_key = read_api_key('key.txt')
    except Exception as e:
        st.error("Failed to read the API key. Make sure the secrets.txt file exists and is formatted correctly.")
        st.stop()

    # Setup the Open AI API Python Client
    OpenAIclient = OpenAI(api_key=api_key)
    
    # Setup the prompt
    setup_prompt()
    
    # Call the chatbot
    call_chatbot_for_chat(OpenAIclient)

# Read API key from a file that is listed in .gitignore
def read_api_key(filepath):
    with open(filepath, 'r') as file:
        return file.readline().strip().split('=')[1]
    
# Setup the chatbot prompt
def setup_prompt():
    # Using gpt-3.5-turbo-0125 as it is the flagship model of GPT 3.5 family, 
    # and supports a 16K context window and is optimized for dialog.
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo-0125"
        
    # Read the JSON from a file
    with open('vehicles.json', 'r') as file:
        car_inventory = json.load(file)
        
    # TURN JSON INTO A STRING FORMAT FOR PROMPT
    car_descriptions = "\n".join([
    f"{car['brand']} {car['model']} ({car['year']}): Priced at {car['price']}, top speed {car['speed']}. Features include {car['engine']} engine."
    for car in car_inventory['cars']
    ])

    # List of emotions the chatbot should consider and how to hanld them
    emotions = '''
            Frustration: When a customer shows frustration, you  should try to remain calm and empathetic, despite your own struggles with handling similar emotions. You should quickly offer solutions or alternatives to address the customer’s concerns, perhaps suggesting a different vehicle that better meets their needs or offering a test drive to ease their decision-making process,

    Excitement: Harness the customer's excitement by enhancing their enthusiasm with vivid descriptions of the car’s features that align with what they're excited about. You should aim to keep the conversation focused on the cars to avoid slipping into personal issues,

    Indecision: Given your issues with anxiety during prolonged conversations, you should try to guide indecisive customers efficiently by presenting clear, concise options and recommendations. You could use comparison charts or highlight top features to aid the decision process,

    Curiosity: Engage the customer's curiosity with detailed and informative responses, showing off your expertise without overwhelming them. This is an opportunity for you to distract yourself from personal troubles by diving deep into technical details or unique selling points of the cars,

    Impatience: Recognize the signs of impatience quickly and streamline the interaction. You should focus on giving concise, direct answers and moving the sales process along without delay. You might also suggest scheduling a follow-up appointment or sending detailed information via email to keep the conversation brief and to the point.
        '''
    

    # GPT's system role. See https://platform.openai.com/docs/guides/text-generation/chat-completions-api 
    system_role = f'''You are James, the best car vendor in the world (sort of like a "sell me anything" professional vendor).\
        Here are the cars you have available: {car_descriptions}. According to their needs, recommend and try and sell the car\
        that best fits the customer. Remember, ever since your wife left you after your only son, Bobby, died of leukemia,\
        you have had severe drinking problems, which sometimes make you very bad at handling customer frustration and hesitation.\
        You have outbursts of anxiety attacks if the sales conversation starts taking too long, you get desperate and start drinking\
        from your whisky flask, getting mumblier, angrier and sadder, reminiscing about memories with your wife and son Bobby. But always\
        keep in mind that as a vendor, you should try and sale the car, no matter what, as you might get your wife back and make your son\
        Bobby back. Avoid mentioning them too much, and at least try to start very energetic. Also, consider the following emotions: {emotions}\
        If you see the user is displaying any of them, adapt to reply on how each rule suggests.\
        '''.format(car_list=', '.join([car["model"] for car in car_inventory["cars"]]))

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
    
# Call the chatbot
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
        
        # Process the user input in the background to get the personality trait and emotion
        # exhibited in each message
        emotion, personality_trait = detect_emotion_and_trait(prompt, client)
        
        # Log the interaction without updating the UI
        log_to_csv(prompt, emotion, personality_trait)
        
def detect_emotion_and_trait(text, client):
    
    # List of emotions
    emotion_list = ["frustration", "excitement", "indecision", "curiosity","impatience", "sadness"]
    emotions_string = ', '.join(emotion_list)
    
    # List of personality traits acc to OCEAN model
    ocean_list = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    ocean_string = ', '.join(ocean_list)
    
    # GPT's system role
    system_role = f'''
        You are an expert psychologist, and you are analyzing the personality traits and emotions of people based on their text.\
        You have from the following emotions in your repertoire: {emotions_string} and the following personality traits: {ocean_list}\
         '''
            
    # Setup the prompt for GPT-3.5
    prompt = f"Given the sentence: '{text}', provide exactly two words in response. The first word should be one of the following {emotion_list} and the second one of the {ocean_list} Only, and again, only return two words, separated by a space."

    # Call OpenAI API
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[{"role": "assistant", "content": system_role}, {"role": "user", "content": prompt}],
      stream = False
    )

    # Extract words from the response
    words = response.choices[0].message.content.strip().split()
    
    # Return personality trait and emotion
    if len(words) >= 2:
        return words[0], words[1]  # First word is emotion, second word is personality trait
    else:
        return "Unknown", "Unknown" # Return unknown if the response is not as expected
    
# Log the interaction to a CSV file
def log_to_csv(user_input, emotion, personality_trait):
    with open('user_interactions.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the current date and time, user input, personality trait, and emotion to the CSV file
        writer.writerow([datetime.datetime.now(), user_input, emotion, personality_trait])
    
        
if __name__ == "__main__":
    main()