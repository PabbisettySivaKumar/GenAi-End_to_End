import streamlit as st
import requests
import json

st.set_page_config(page_title="Generative AI RAG App", layout="wide")
st.title("Generative AI RAG System")
st.caption("Upload PDFs → Build Knowledge Graph → Ask Questions")

BACKEND_URL = "http://127.0.0.1:8000"  # Adjust if backend runs elsewhere


st.header("Upload Your PDFs")

project_name = st.text_input("Project Name", value="default_project")
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    help="Hold Ctrl (Windows) or Cmd (Mac) to select multiple files."
)

if st.button("Upload PDFs"):
    if not uploaded_files:
        st.warning("Please select at least one PDF file.")
    else:
        with st.spinner("Uploading and processing your PDFs..."):
            files_payload = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/upload",
                    files=files_payload,
                    data={"project_name": project_name},
                    timeout=300
                )
                if response.status_code == 200:
                    st.success("Upload successful!")
                    #st.json(response.json())
                else:
                    st.error(f"Upload failed: {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")


st.header("Ask a Question")

query_text = st.text_area("Enter your question here", placeholder="e.g., What are transformers in deep learning?")

if st.button("Get Answer"):
    if not query_text.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Querying your knowledge base..."):
            try:
                payload = {"query": query_text}
                res = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=120)
                if res.status_code == 200:
                    answer = res.json().get("answer", "No answer returned.")
                    st.subheader("Answer:")
                    st.write(answer)
                else:
                    st.error(f"Query failed: {res.status_code}")
                    st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Powered by FastAPI • LangChain • Ollama • Neo4j • MongoDB")
