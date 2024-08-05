import streamlit as st
import requests

st.set_page_config(page_title="Chatbot Game", page_icon=":speech_balloon:", layout="wide")

st.title("Chatbot Game")

def get_response(message, chat_history):
    response = requests.post('http://localhost:5000/', json={
        'message': message,
        'messages': chat_history
    })
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error fetching response from backend")
        return None

def transcribe_audio(file):
    response = requests.post('http://localhost:5000/transcribe', files={'audio_file': file})
    if response.status_code == 200:
        return response.json().get('text', 'Transcription failed')
    else:
        st.error("Error transcribing audio")
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
    st.session_state.transcription_text = transcription
