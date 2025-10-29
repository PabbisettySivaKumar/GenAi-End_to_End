import streamlit as st
import requests
import tempfile

st.set_page_config(
    page_title="Generative AI RAG System",
    layout="centered"
)

st.markdown("""
<style>
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

    header[data-testid="stHeader"] {
        display: none !important;
    }

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

BACKEND_URL = "http://127.0.0.1:8000"

st.markdown("""
<div style="text-align:center; margin-bottom:2rem;">
    <h1>Generative AI RAG System</h1>
    <p>Upload PDFs → Build Knowledge Graph → Chat with your Knowledge Base</p>
</div>
""", unsafe_allow_html=True)

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

st.subheader("Chat with Your Knowledge Base")
st.caption("Ask follow-up questions and continue the conversation")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for role, msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if role == "user" else "bot-bubble"
    st.markdown(f'<div class="chat-bubble {bubble_class}">{msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns([8, 2])

if "input_key_counter" not in st.session_state:
    st.session_state.input_key_counter = 0

dynamic_key = f"user_message_input_{st.session_state.input_key_counter}"

user_message = col1.text_input(
    "Type your message",
    key=dynamic_key,
    placeholder="Ask something about your PDFs..."
)
send = col2.button("Send")

if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.session_state.last_chunks = []
    st.rerun()

if send and user_message.strip():
    st.session_state.chat_history.append(("user", user_message))
    with st.spinner("Thinking..."):
        try:
            payload = {"query": user_message, "project_name": project_name}
            res = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)

            if res.status_code == 200:
                data = res.json()
                answer = data.get("answer", "No answer returned.")
                st.session_state.chat_history.append(("bot", answer))
                st.session_state.last_chunks = data.get("chunks", [])
            else:
                st.session_state.chat_history.append(("bot", f"Query failed: {res.status_code}"))
                st.session_state.last_chunks = []
        except Exception as e:
            st.session_state.chat_history.append(("bot", f"Error: {e}"))
            st.session_state.last_chunks = []

    st.session_state.input_key_counter += 1
    st.rerun()

if st.session_state.last_chunks:
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("🔍 Retrieved Contexts with Highlights")

    for idx, chunk in enumerate(st.session_state.last_chunks):
        st.markdown(f"**Chunk {idx + 1} — Page {chunk.get('page_num')}**")
        st.caption(chunk.get("text", "")[:300] + "...")

        payload = {
            "pdf_path": chunk.get("pdf_path"),
            "page_num": chunk.get("page_num"),
            "snippet": chunk.get("text", "")[:100]
        }

        try:
            highlight_res = requests.post(f"{BACKEND_URL}/pdf/highlight", json=payload)
            if highlight_res.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmp.write(highlight_res.content)
                tmp.flush()
                st.image(tmp.name, caption=f"Page {chunk.get('page_num')} Highlight", use_column_width=True)
            else:
                st.warning(f"Could not generate highlight for page {chunk.get('page_num')}.")
        except Exception as e:
            st.warning(f"Error generating highlight: {e}")

st.markdown("""
<div class="footer">
    Powered by <b>FastAPI</b> • <b>LangChain</b> • <b>Ollama</b> • <b>Neo4j</b> • <b>MongoDB</b><br>
    <a href="https://x.com/itsPSK95" target="_blank" style="text-decoration:none; color:#3b82f6; font-weight:500;">
        🕊️ Follow me on X
    </a>
</div>
""", unsafe_allow_html=True)
