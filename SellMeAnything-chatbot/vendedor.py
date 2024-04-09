import requests
import json

model = 'mistral:latest'

# Initial context
context = []

# Placeholder function for sentiment analysis
def infer_psychological_state(message):
    positive_keywords = ['love', 'like', 'enjoy']
    negative_keywords = ['hate', 'dislike', 'bad']
    if any(word in message for word in positive_keywords):
        return 'positive'
    elif any(word in message for word in negative_keywords):
        return 'negative'
    else:
        return 'neutral'

def generate(prompt, context, top_k, top_p, temp):
    r = requests.post('http://localhost:11434/api/generate',
                      json={
                          'model': model,
                          'prompt': prompt,
                          'context': context,
                          'options': {
                              'top_k': top_k,
                              'temperature': temp,
                              'top_p': top_p
                          }
                      },
                      stream=False)
    r.raise_for_status()

    response = ""

    for line in r.iter_lines():
        body = json.loads(line)
        response_part = body.get('response', '')
        if 'error' in body:
            raise Exception(body['error'])

        response += response_part

        if body.get('done', False):
            context = body.get('context', [])
            return response, context

def chat():
    global context
    while True:
        input_text = input("You: ")
        if input_text.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            break

        psychological_state = infer_psychological_state(input_text)

        if psychological_state == 'positive':
            prompt = f"Respond with enthusiasm. Customer is happy: {input_text}"
        elif psychological_state == 'negative':
            prompt = f"Respond with empathy and offer support. Customer seems unhappy: {input_text}"
        else:  # Neutral
            prompt = f"Maintain a charismatic and engaging tone: {input_text}"

        try:
            top_k = 40
            top_p = 0.9
            temp = 0.8

            output_text, context = generate(prompt, context, top_k, top_p, temp)
            print("Bot:", output_text)
        except Exception as e:
            print("An error occurred:", e)
            break

if __name__ == "__main__":
    print("Starting sales bot with a charismatic personality. Type 'exit' or 'quit' to stop.")
    chat()
