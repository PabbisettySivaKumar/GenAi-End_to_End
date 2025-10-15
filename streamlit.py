import streamlit as st
import requests

st.title("Generative PDF Query Application")
files= st.file_uploader("Upload PDF's", type= "pdf", accept_multiple_files= True)
if files:
    uploaded= requests.post("http://localhost:8000/upload", files= [("files", f) for f in files])
    st.success(uploaded.json())

query= st.text_input("Ask a qustion about ypur PDF's")
if st.button("Query"):
    res= requests.post("http://localhost:8000/query", json={"query": query})
    st.write(res.json()["answer"])