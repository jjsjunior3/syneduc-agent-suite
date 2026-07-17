import streamlit as st
import requests
import uuid

API_URL = "http://supervisor:8000/chat"

st.set_page_config(page_title="SynerEduc — Assistente Comercial", page_icon="🎓")

st.title("🎓 SynerEduc — Assistente Comercial")
st.caption("Tire dúvidas sobre planos ou avance para fechar uma proposta.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Digite sua mensagem")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "message": user_input,
        "session_id": st.session_state.session_id,
        "client_id": "streamlit-demo",
    }

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                resposta = data.get("resposta", "Erro na resposta do servidor")
            else:
                resposta = "Erro ao chamar API"

            st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})