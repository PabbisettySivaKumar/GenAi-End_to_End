import streamlit as st
import requests

st.set_page_config(
    page_title="Generative AI RAG System",
    layout="centered"
)

st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
        padding-top: 1rem;
    }

    /* Typography */
    h1, h2, h3 {
        color: #111111;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    p, label, .stTextInput label, .stTextArea label {
        color: #5f5f5f !important;
        font-size: 0.93rem !important;
    }

    /* Input Boxes */
    .stTextInput > div > div > input, .stTextArea textarea {
        background-color: #fafafa !important;
        border-radius: 10px !important;
        border: 1px solid #e5e5e5 !important;
        padding: 0.7rem 1rem !important;
        color: #1f1f1f !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border: 1px solid #bfbfbf !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Card Containers */
    .card {
        background-color: #ffffff;
        border: 1px solid #eaeaea;
        border-radius: 12px;
        padding: 2rem 2.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        margin-bottom: 2rem;
    }

    /* Buttons - clean neutral look */
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

    /* --- File uploader styling fixes --- */
    [data-testid="stFileUploader"] section {
        background-color: #f9f9f9 !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] section div {
        color: #111 !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploaderFileName"] {
        color: #1f1f1f !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #fafafa !important;
        border: 1px dashed #dcdcdc !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploaderDropzone"] div div {
        color: #5f5f5f !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #7a7a7a;
        font-size: 0.85rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #efefef;
    }

    /* Title Section */
    .title-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    .title-icon {
        background-color: #f5f5f5;
        color: #111;
        font-size: 1.5rem;
        padding: 0.8rem;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    /* Fix for "Browse files" button appearing black */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #f5f5f5 !important;
        color: #111 !important;
        border: 1px solid #dcdcdc !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #ebebeb !important;
        border-color: #cfcfcf !important;
        transform: translateY(-1px);
    }
    /* Hide Streamlit default black header bar */
header[data-testid="stHeader"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

st.markdown("""
<div class="title-container">
    <h1>Generative AI RAG System</h1>
    <p>Upload PDFs → Build Knowledge Graph → Ask Questions</p>
</div>
""", unsafe_allow_html=True)

st.subheader("📂 Upload Your PDFs")
st.caption("Build your knowledge base from documents")

project_name = st.text_input("Project Name", value="default_project")
uploaded_files = st.file_uploader(
    "PDF Files",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("📁 Upload PDFs"):
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
                    st.success("✅ Upload successful! Your knowledge graph is ready.")
                else:
                    st.error(f"Upload failed: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Error: {e}")
st.markdown('</div>', unsafe_allow_html=True)

st.subheader("💬 Ask a Question")
st.caption("Query your knowledge base using AI")

query_text = st.text_area("Your Question", placeholder="e.g., What are transformers in deep learning?")
if st.button("💡 Get Answer"):
    if not query_text.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Querying your knowledge base..."):
            try:
                payload = {"query": query_text}
                res = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)
                if res.status_code == 200:
                    answer = res.json().get("answer", "No answer returned.")
                    st.markdown("### 🧠 Answer:")
                    st.success(answer)
                else:
                    st.error(f"Query failed: {res.status_code}")
                    st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    Powered by <b>FastAPI</b> • <b>LangChain</b> • <b>Ollama</b> • <b>Neo4j</b> • <b>MongoDB</b><br>
    <a href="https://x.com/itsPSK95" target="_blank" style="text-decoration:none; color:#3b82f6; font-weight:500;">
        🕊️ Follow me on X
    </a>
</div>
""", unsafe_allow_html=True)