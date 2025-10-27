import streamlit as st
import requests

# -----------------------------------------------------------
# Page Setup
# -----------------------------------------------------------
st.set_page_config(
    page_title="Generative AI RAG System",
    layout="centered"
)

# -----------------------------------------------------------
# Custom CSS Styling
# -----------------------------------------------------------
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
        padding-top: 1rem;
    }

    h1, h2, h3 {
        color: #111111;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    p, label {
        color: #5f5f5f !important;
        font-size: 0.93rem !important;
    }

    /* Input Boxes */
    .stTextInput > div > div > input {
        background-color: #fafafa !important;
        border-radius: 10px !important;
        border: 1px solid #e5e5e5 !important;
        padding: 0.7rem 1rem !important;
        color: #1f1f1f !important;
        caret-color: #111 !important;
    }

    .stTextInput > div > div > input:focus {
        border: 1px solid #bfbfbf !important;
        outline: none !important;
        box-shadow: 0 0 0 1px #bfbfbf !important;
    }

    /* Buttons */
    .stButton button {
        width: 100%;
        background-color: #f5f5f5 !important;
        color: #111111 !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border: 1px solid #dcdcdc !important;
        padding: 0.7rem 1rem !important;
        transition: all 0.15s ease-in-out;
    }

    .stButton button:hover {
        background-color: #ebebeb !important;
        transform: translateY(-1px);
        border-color: #cfcfcf !important;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] section {
        background-color: #f9f9f9 !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background-color: #fafafa !important;
        border: 1px dashed #dcdcdc !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background-color: #f5f5f5 !important;
        color: #111 !important;
        border: 1px solid #dcdcdc !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.8rem !important;
        font-weight: 500 !important;
        opacity: 1 !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #ebebeb !important;
        border-color: #cfcfcf !important;
        transform: translateY(-1px);
    }

    [data-testid="stFileUploaderFileName"] {
        color: #111 !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }

    /* Hide Streamlit default header */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Chat Styling */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #eaeaea;
        border-radius: 12px;
        background-color: #fafafa;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .chat-bubble {
        display: inline-block;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        max-width: 80%;
        line-height: 1.4;
    }

    .user-bubble {
        background-color: #e6f0ff;
        color: #111;
        margin-left: auto;
        display: block;
        text-align: right;
    }

    .bot-bubble {
        background-color: #f5f5f5;
        color: #111;
        margin-right: auto;
        display: block;
        text-align: left;
    }

    .footer {
        text-align: center;
        color: #7a7a7a;
        font-size: 0.85rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #efefef;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Backend URL
# -----------------------------------------------------------
BACKEND_URL = "http://127.0.0.1:8000"

# -----------------------------------------------------------
# Title
# -----------------------------------------------------------
st.markdown("""
<div style="text-align:center; margin-bottom:2rem;">
    <h1>Generative AI RAG System</h1>
    <p>Upload PDFs → Build Knowledge Graph → Chat with your Knowledge Base</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Upload Section
# -----------------------------------------------------------
st.subheader("Upload Your PDFs")
st.caption("Build your knowledge base from documents")

project_name = st.text_input("Project Name", value="default_project")

uploaded_files = st.file_uploader(
    "PDF Files",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("Upload PDFs"):
    if not uploaded_files:
        st.warning("Please select at least one PDF file.")
    else:
        with st.spinner("Uploading and processing your PDFs..."):
            try:
                files_payload = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
                response = requests.post(
                    f"{BACKEND_URL}/api/upload",
                    files=files_payload,
                    data={"project_name": project_name},
                    timeout=300
                )
                if response.status_code == 200:
                    st.success("Upload successful! Your knowledge graph is ready.")
                else:
                    st.error(f"Upload failed: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Error: {e}")

# -----------------------------------------------------------
# Chat Section
# -----------------------------------------------------------
st.subheader("Chat with Your Knowledge Base")
st.caption("Ask follow-up questions and continue the conversation")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for role, msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if role == "user" else "bot-bubble"
    st.markdown(f'<div class="chat-bubble {bubble_class}">{msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Input and Send Section (Fixed)
# -----------------------------------------------------------
col1, col2 = st.columns([8, 2])

# Counter for unique input key
if "input_key_counter" not in st.session_state:
    st.session_state.input_key_counter = 0

# ✅ Use dynamic key properly here
dynamic_key = f"user_message_input_{st.session_state.input_key_counter}"

user_message = col1.text_input(
    "Type your message",
    key=dynamic_key,  # ✅ Corrected line
    placeholder="Ask something about your PDFs..."
)
send = col2.button("Send")

if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()

if send and user_message.strip():
    st.session_state.chat_history.append(("user", user_message))
    with st.spinner("Thinking..."):
        try:
            payload = {"query": user_message, "project_name": project_name}
            res = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)
            if res.status_code == 200:
                answer = res.json().get("answer", "No answer returned.")
                st.session_state.chat_history.append(("bot", answer))
            else:
                st.session_state.chat_history.append(("bot", f"Query failed: {res.status_code}"))
        except Exception as e:
            st.session_state.chat_history.append(("bot", f"Error: {e}"))
    # ✅ Increment counter → new input key next render → clears box
    st.session_state.input_key_counter += 1
    st.rerun()

# -----------------------------------------------------------
# Footer
# -----------------------------------------------------------
st.markdown("""
<div class="footer">
    Powered by <b>FastAPI</b> • <b>LangChain</b> • <b>Ollama</b> • <b>Neo4j</b> • <b>MongoDB</b><br>
    <a href="https://x.com/itsPSK95" target="_blank" style="text-decoration:none; color:#3b82f6; font-weight:500;">
        🕊️ Follow me on X
    </a>
</div>
""", unsafe_allow_html=True)
