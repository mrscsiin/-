import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
import threading
import time
import streamlit as st
import requests

# OpenAI API Key 설정
openai.api_key = "sk-VEeUuMyarMIAG9l0tiRBN751xT4feVWBy6pGuvWgzKT3BlbkFJPTu-muMFjWytZ0qHPt3MzwMUbli95oqlAQLisTlGcA"

# Flask 앱 생성
app = Flask(__name__)
CORS(app)  # CORS 설정을 통해 다른 도메인에서 접근 허용
app.secret_key = os.urandom(24)

# Flask에서 사용할 프로ンプ트
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'messages' not in session:
        session['messages'] = [{"role": "system", "content": prompt}]

    user_input = None
    response = None
    if request.method == 'POST':
        user_input = request.form['message']
        session['messages'].append({"role": "user", "content": user_input})
        response = chat(session['messages'])
        session['messages'].append({"role": "assistant", "content": response})

    return render_template('index.html', user_input=user_input, response=response, chat_history=session['messages'])

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # 임시 파일로 저장
        file_name = "tmp_audio_file.wav"
        audio_file.save(file_name)

        # Whisper API를 사용하여 음성 인식
        with open(file_name, "rb") as f:
            transcription = openai.Audio.transcribe("whisper-1", f, language="ko")

        text = transcription['text']
    except Exception as e:
        print(e)
        text = f"음성인식에서 실패했습니다. {e}"
    finally:
        # 임시 파일 삭제
        if os.path.exists(file_name):
            os.remove(file_name)

    return jsonify({"text": text})

def chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content']

# Streamlit 앱 생성
def streamlit_app():
    st.set_page_config(page_title="Chatbot Game", page_icon=":speech_balloon:", layout="wide")

    st.title("Chatbot Game")

    def get_response(message, chat_history):
        try:
            response = requests.post('http://localhost:5000/', json={
                'message': message,
                'messages': chat_history
            })
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching response from backend: {e}")
            return None

    def transcribe_audio(file):
        try:
            response = requests.post('http://localhost:5000/transcribe', files={'audio_file': file})
            response.raise_for_status()
            return response.json().get('text', 'Transcription failed')
        except requests.exceptions.RequestException as e:
            st.error(f"Error transcribing audio: {e}")
            return 'An error occurred'

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [{"role": "system", "content": "You are the host of an interactive horror game. Interact with the player to guide them through the game."}]

    if 'transcription_text' not in st.session_state:
        st.session_state.transcription_text = ""

    st.text_area("Chat History", value="\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history]), height=300)

    user_input = st.text_input("Type a message", value=st.session_state.transcription_text)

    if st.button("Send"):
        response = get_response(user_input, st.session_state.chat_history)
        if response:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": response['response']})
            st.text_area("Chat History", value="\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history]), height=300)
            st.session_state.transcription_text = ""

    uploaded_file = st.file_uploader("Upload an audio file", type=["wav"])
    if uploaded_file is not None:
        transcription = transcribe_audio(uploaded_file)
        st.text_area("Transcription Result", value=transcription)
        st.session_state.transcription_text = ""

def run_flask():
    app.run(port=5000, threaded=True)

def run_streamlit():
    st.write("Streamlit 앱이 실행됩니다. 브라우저에서 http://localhost:8501 확인하세요.")
    streamlit_app()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    streamlit_thread = threading.Thread(target=run_streamlit)

    flask_thread.start()
    time.sleep(2)  # Flask 서버가 시작될 때까지 대기
    streamlit_thread.start()
