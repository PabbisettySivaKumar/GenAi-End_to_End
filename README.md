# 🚀 Generative AI RAG System

This repository implements an **end-to-end Retrieval-Augmented Generation (RAG)** system that integrates **Ollama LLM**, **Neo4j Vector Database**, and **Langfuse** for prompt management and observability. It includes a **Streamlit-based UI**, modular backend services, and PDF ingestion capabilities.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Ollama](https://img.shields.io/badge/LLM-Ollama-1F1F1F)
![Neo4j](https://img.shields.io/badge/VectorDB-Neo4j-008CC1)
![Langfuse](https://img.shields.io/badge/Prompt-Langfuse-6E56CF)

---

## 🧠 Overview

The system enables users to:
- Upload and process PDFs.
- Chunk and embed documents using Ollama embeddings.
- Store and retrieve embeddings via Neo4j.
- Query the system to retrieve relevant chunks and generate AI responses.
- Track and monitor prompt performance with Langfuse.
- Interact via an elegant Streamlit frontend.

---

## 🏗️ Project Structure

```
GenerativeApplication/
├── streamlit.py          # Streamlit frontend interface for user interaction
├── main.py               # FastAPI entry point for handling requests and routing
├── services/
│   ├── chunking.py       # Splits PDF text into manageable semantic chunks
│   ├── querying.py       # Retrieves top relevant chunks and generates responses
│   ├── storage.py        # Handles Neo4j vector storage and retrieval
│   ├── embeddings.py     # Embedding creation using Ollama models
│   └── pdf_utils.py      # PDF reading and text extraction
├── router/
│   ├── pdf_upload.py     # Handles PDF upload and storage routing
│   └── pdf_render.py     # Converts and visualizes PDFs for UI display
├── utils/
│   └── embeddings.py     # Helper functions for managing embeddings
├── .env                  # Environment variables (Ollama, Neo4j, Langfuse)
├── requirements.txt      # All dependencies required for the project
└── README.md             # Project documentation
```

---

## ⚙️ Key Components

### 1. **Frontend – `streamlit.py`**
- Provides a clean Streamlit UI.
- Allows users to upload PDFs and query them.
- Displays AI-generated answers from the RAG pipeline.

### 2. **Core Logic**
- **`main.py`** — Orchestrates routing between components using FastAPI.
- **`querying.py`** — Implements the retrieval + generation pipeline.
- **`chunking.py`** — Splits documents into context-preserving chunks.
- **`storage.py`** — Connects to Neo4j and manages vector storage.
- **`embeddings.py`** — Generates text embeddings using Ollama models.

### 3. **PDF Management**
- **`pdf_upload.py`** — Handles incoming PDF uploads from the frontend.
- **`pdf_utils.py`** — Extracts clean text content from PDFs.
- **`pdf_render.py`** — Renders PDF preview for the UI.

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| LLM | Ollama |
| Embeddings | Ollama Embeddings |
| Vector DB | Neo4j |
| Prompt Management | Langfuse |
| Backend | FastAPI |
| Frontend | Streamlit |
| Storage | Local/TempFile + Neo4j |
| Logging | Python logging module |

---

## 🚀 How to Run

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/GenerativeApplication.git
cd GenerativeApplication
```

### 2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Configure Environment Variables**
Create a `.env` file with:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=DB_NAME
MONGODB_COLLECTION=COLLECTION_NAME

OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
OLLAMA_LLM_MODEL=llama3.1:8b

LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PROMPT_NAME=prompt_template_name
```

### 5. **Run/Initialize LLM Model**
```bash
ollama serve
```

### 6. **Run Backend**
```bash
uvicorn main:app --reload
```

### 7. **Run Frontend**
```bash
streamlit run streamlit.py
```

---

## 📊 Example Workflow

1. Upload a PDF using Streamlit.  
2. Backend extracts and chunks the text.  
3. Embeddings are generated and stored in Neo4j.  
4. User queries a question.  
5. The system retrieves relevant chunks, generates a contextual answer, displays the page number, and highlights the chunks in the UI.  

---

## 🧪 Logging & Observability
All services use Python’s logging module with tagged namespaces (e.g., `[services.querying]`, `[router.pdf_upload]`).  
Langfuse is integrated for tracking prompt and response metrics.

---

## 🧱 Future Enhancements
- Add hybrid search (semantic + keyword)  
- Integrate multiple Ollama models for comparison  
- Introduce user authentication and query history  
- Deploy on Docker and Streamlit Cloud  

---

## 👨‍💻 Author  

<table>
  <tr>
    <td>
      <strong>Siva Kumar</strong><br>
      <em>Generative AI RAG System Developer</em><br><br>
      <a href="https://x.com/itsPSK95" target="_blank">
        <img src="https://img.shields.io/badge/Twitter-@yourhandle-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter Badge">
      </a>
      <br><br>
      📅 <strong>Last updated:</strong> October 2025  
    </td>
  </tr>
</table>

---

## 🪪 License
This project is licensed under the **MIT License**.