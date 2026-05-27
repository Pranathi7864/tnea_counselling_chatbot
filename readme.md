# TNEA Counselling RAG Assistant

A hybrid Retrieval-Augmented Generation (RAG) chatbot designed to assist students during the Tamil Nadu Engineering Admissions (TNEA) counselling process. The system answers questions related to college prediction, cutoff marks, branch selection, eligibility, reservation, counselling procedure, and college details using verified counselling documents and previous year cutoff data.

---

## Overview

TNEA counselling involves comparing colleges, branches, cutoff marks, eligibility rules, reservation categories, and counselling procedures. This project simplifies that process by providing an AI-powered chatbot that retrieves relevant information from official-style documents and structured cutoff data, then generates a clear student-friendly response using Gemini.

The chatbot is built to support queries such as:

- “I have 145 cutoff. What college will I get near Coimbatore?”
- “What is the eligibility criteria for TNEA?”
- “What do you think about PSG College?”
- “Which course is suitable if I am interested in data handling?”
- “What certificates are required for counselling?”

---

## Key Features

- Cutoff-based college prediction using previous year data
- College and branch recommendation based on student interests
- Location-based college filtering
- College details and cutoff lookup
- Counselling eligibility and procedure-based question answering
- Hybrid retrieval using structured Excel data and FAISS vector search
- Gemini-powered answer generation
- Chatbot-style web interface
- Browser-based chat history saving

---

## Tech Stack

**Backend:** Python, Flask  
**Frontend:** HTML, CSS, JavaScript  
**Data Processing:** pandas, openpyxl, pdfplumber  
**Embeddings:** Sentence Transformers  
**Vector Database:** FAISS  
**LLM:** Google Gemini API  
**Environment Management:** python-dotenv  

---

## System Workflow

```text
User Query
   ↓
Query Router
   ↓
Retriever
   ├── Excel-based search for cutoff and college prediction
   ├── Fuzzy college search for college details
   └── FAISS vector search for counselling documents
   ↓
Retrieved Context
   ↓
Gemini API
   ↓
Final Student-Friendly Answer

## Installation

```bash
git clone https://github.com/your-username/tnea-rag.git
cd tnea-rag
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
GEMINI_API_KEY=your_api_key_here
Usage
python src/ingest.py
python src/embeddings.py
python src/app.py
Open in browser:
http://127.0.0.1:5000
Hybrid RAG Workflow
User Query
   ↓
Query Router
   ↓
Retriever
   ├── Excel Search
   │      ├── Cutoff prediction
   │      ├── Category-based filtering
   │      ├── Branch-based filtering
   │      └── Location-based filtering
   │
   ├── Fuzzy College Search
   │      └── College name/details lookup
   │
   └── FAISS Vector Search
          ├── Eligibility questions
          ├── Counselling rules
          ├── Reservation details
          └── Certificate-related queries
   ↓
Retrieved Context
   ↓
Gemini API
   ↓
Structured Student-Friendly Answer
Why Hybrid RAG?
Normal RAG:
User Query → Vector Search → LLM Answer
Problem:
Vector search is good for document questions,
but it may give inaccurate results for numerical cutoff queries.
Hybrid RAG:
Structured Excel Search + FAISS Document Search + Gemini Answer Generation
Benefits:
- More accurate cutoff prediction
- Better college filtering
- Reliable document-based answers
- Gemini gives only the final structured explanation