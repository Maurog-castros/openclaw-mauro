import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(page_title="OpenClaw Dashboard", page_icon="🤖", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stSidebar {
        background-color: #ffffff;
        border-right: 1px solid #e6e9ef;
    }
    </style>
    """, unsafe_allow_stdio=True)

# Sidebar: Configuración de Modelos y Sistema
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Selección de Modelo
    st.subheader("Modelo")
    # Intentar obtener modelos de LiteLLM, si falla usar lista por defecto
    try:
        client_models = OpenAI(
            base_url=f"http://{os.getenv('UBUNTU_SRV_IP', '192.168.1.12')}:4000/v1",
            api_key=os.getenv('LITELLM_MASTER_KEY', 'sk-openclaw-local')
        )
        available_models = [m.id for m in client_models.models.list().data]
    except Exception as e:
        available_models = [
            "openclaw-auto",
            "openclaw-remote-qwen",
            "openclaw-remote-coder",
            "openclaw-gemini-flash",
            "openclaw-openai-fast"
        ]
    
    selected_model = st.selectbox(
        "Selecciona el modelo para esta sesión:",
        available_models,
        index=0
    )
    
    st.divider()
    
    # Prompt de Sistema
    st.subheader("📝 Prompt de Sistema")
    system_prompt = st.text_area(
        "Define el comportamiento del agente:",
        value="Eres un asistente experto en ayudar a PYMES y emprendedores en Chile. Tu objetivo es proporcionar información clara, útil y accionable.",
        height=200
    )
    
    if st.button("Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(
                base_url=f"http://{os.getenv('UBUNTU_SRV_IP', '192.168.1.12')}:4000/v1",
                api_key=os.getenv('LITELLM_MASTER_KEY', 'sk-openclaw-local')
            )
            
            # Construir mensajes incluyendo el prompt de sistema
            messages = [{"role": "system", "content": system_prompt}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            
            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            # Agregar respuesta al historial
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error al conectar con LiteLLM: {str(e)}")
            st.info("Asegúrate de que el túnel SSH o la conexión al servidor 192.168.1.12:4000 esté activa.")
