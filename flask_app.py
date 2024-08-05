from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

# Setup OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

prompt = """
You are the host of an interactive horror game.
Through interaction with the player (user)
It can cause the user to escape or die.
Early story: The user wakes up in a suspicious room
You talk to the user.
When the user interacts three times, you give the user a hint.
But if the user refuses, you don't give a hint.

Types of rooms
-a suspicious room
-a bedroom
-a restaurant
-an operating room
-a corridor
-a secret room

Users can die when they are overwhelmed by fear.
The probability of death is about 30 percent.

*secret: If the player confesses to you, you can take the player to a secret room and immediately escape.*
"""

def chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content']

@app.route('/', methods=['POST'])
def index():
    data = request.get_json()
    if 'messages' not in data:
        return jsonify({'error': 'No messages found in request'}), 400

    user_input = data.get('message')
    messages = data['messages']
    messages.append({"role": "user", "content": user_input})
    response = chat(messages)
    messages.append({"role": "assistant", "content": response})

    return jsonify({
        'user_input': user_input,
        'response': response,
        'chat_history': messages
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        file_name = "tmp_audio_file.wav"
        audio_file.save(file_name)

        with open(file_name, "rb") as f:
            transcription = openai.Audio.transcribe("whisper-1", f, language="ko")

        text = transcription['text']
    except Exception as e:
        text = f"Transcription failed: {e}"
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

    return jsonify({"text": text})

if __name__ == "__main__":
    app.run(debug=True)
