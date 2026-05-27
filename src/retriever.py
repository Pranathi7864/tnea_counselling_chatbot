"""
retriever.py
------------
Hybrid Retriever for TNEA RAG

1. Cutoff prediction queries  -> Excel filtering
2. Exact cutoff queries       -> Excel exact search
3. General counselling rules  -> FAISS/PDF search
"""

import os
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz
from embeddings import load_vector_store, MODEL_NAME

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_FILE = os.path.join(DATA_DIR, "tnea 2025.xlsx")

TOP_K = 5

CATEGORIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
TN_DISTRICTS = [
    "ariyalur", "chengalpattu", "chennai", "coimbatore", "cuddalore",
    "dharmapuri", "dindigul", "erode", "kallakurichi", "kanchipuram",
    "kanyakumari", "karur", "krishnagiri", "madurai", "mayiladuthurai",
    "nagapattinam", "namakkal", "nilgiris", "perambalur", "pudukkottai",
    "ramanathapuram", "ranipet", "salem", "sivaganga", "tenkasi",
    "thanjavur", "theni", "thoothukudi", "tiruchirappalli", "trichy",
    "tirunelveli", "tirupathur", "tiruppur", "tirupur", "tiruvallur",
    "tiruvannamalai", "tiruvarur", "vellore", "viluppuram", "virudhunagar"
]


NEARBY_DISTRICTS = {
    "coimbatore": ["coimbatore", "tirupur", "tiruppur", "erode", "nilgiris"],
    "chennai": ["chennai", "chengalpattu", "kanchipuram", "tiruvallur"],
    "madurai": ["madurai", "dindigul", "sivaganga", "virudhunagar", "theni"],
    "salem": ["salem", "namakkal", "erode", "dharmapuri"],
    "trichy": ["trichy", "tiruchirappalli", "perambalur", "pudukkottai", "thanjavur"],
}

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def clean_cutoff(value):
    if pd.isna(value):
        return None

    value = str(value).replace("*", "").strip()

    if value == "" or value.lower() == "nan":    
        return None

    try:
        return float(value)
    except ValueError:
        return None
    


def load_cutoff_df() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    df["college_norm"] = df["College Name"].apply(_norm)
    df["branch_norm"] = df["Branch"].apply(_norm)

    return df


def detect_category(query: str) -> str | None:
    q = query.upper()

    for cat in CATEGORIES:
        if re.search(rf"\b{cat}\b", q):
            return cat

    return None


def detect_branch(query: str) -> str | None:
    q = _norm(query)
    words = set(q.split())

    if "cse" in words or "cs" in words:
        return "COMPUTER SCIENCE AND ENGINEERING"

    if "ece" in words:
        return "ELECTRONICS AND COMMUNICATION ENGINEERING"

    if "eee" in words:
        return "ELECTRICAL AND ELECTRONICS ENGINEERING"

    if "it" in words:
        return "INFORMATION TECHNOLOGY"

    phrase_aliases = {
        "computer science": "COMPUTER SCIENCE AND ENGINEERING",
        "information technology": "INFORMATION TECHNOLOGY",
        "ai ml": "Artificial Intelligence and Machine Learning",
        "aiml": "Artificial Intelligence and Machine Learning",
        "civil": "CIVIL ENGINEERING",
        "mechanical": "MECHANICAL ENGINEERING",
    }

    for alias, branch in phrase_aliases.items():
        if _norm(alias) in q:
            return branch

    return None
def detect_interest_branches(query: str) -> list[str]:
    q = _norm(query)

    interest_map = {
        "data": [
            "computer science",
            "information technology",
            "artificial intelligence",
            "data science",
            "ai and data science",
            "ai and machine learning"
        ],
        "data handling": [
            "computer science",
            "information technology",
            "artificial intelligence",
            "data science",
            "ai and data science",
            "ai and machine learning"
        ],
        "coding": [
            "computer science",
            "information technology"
        ],
        "software": [
            "computer science",
            "information technology"
        ],
        "programming": [
            "computer science",
            "information technology"
        ],
        "electronics": [
            "electronics and communication",
            "electrical and electronics"
        ],
        "hardware": [
            "electronics and communication",
            "electrical and electronics"
        ],
        "construction": [
            "civil"
        ],
        "building": [
            "civil"
        ],
        "machines": [
            "mechanical"
        ],
        "automobile": [
            "mechanical",
            "automobile"
        ],
    }

    matched_branches = []

    for interest, branches in interest_map.items():
        if interest in q:
            matched_branches.extend(branches)

    return list(set(matched_branches))

def detect_location(query: str) -> str | None:
    q = _norm(query)

    for district in TN_DISTRICTS:
        if re.search(rf"\b{district}\b", q):
            return district

    return None


def get_location_filter_words(query: str) -> list[str]:
    location = detect_location(query)

    if not location:
        return []

    return NEARBY_DISTRICTS.get(location, [location])

def extract_cutoff_mark(query: str) -> float | None:
    marks = re.findall(r"\b\d{2,3}(?:\.\d+)?\b", query)

    for mark in marks:
        value = float(mark)
        if 0 <= value <= 200:
            return value

    return None


def is_general_pdf_query(query: str) -> bool:
    q_words = set(_norm(query).split())

    pdf_words = {
        "eligibility",
        "criteria",
        "reservation",
        "procedure",
        "certificate",
        "certificates",
        "counselling",
        "counseling",
        "application",
        "apply",
        "rule",
        "rules",
        "fee",
        "fees",
        "round",
        "choice",
        "allotment",
    }

    return bool(q_words.intersection(pdf_words))


def is_prediction_query(query: str) -> bool:
    q_words = set(_norm(query).split())
    mark = extract_cutoff_mark(query)

    prediction_words = {
        "get",
        "college",
        "colleges",
        "available",
        "possible",
        "predict",
        "prediction",
        "eligible",
        "chance",
        "chances",
        "cutoff",
        "cut",
        "mark",
        "marks",
    }

    return mark is not None and bool(q_words.intersection(prediction_words))


def is_cutoff_query(query: str) -> bool:
    if is_general_pdf_query(query):
        return False

    q_words = set(_norm(query).split())

    cutoff_words = {
        "cutoff",
        "cut",
        "marks",
        "rank",
        "college",
        "colleges",
        "top",
        "best",
    }

    return bool(q_words.intersection(cutoff_words))


def extract_college_words(query: str) -> list[str]:
    stop = {
        "what", "is", "the", "cutoff", "marks", "mark", "for", "in", "of",
        "college", "colleges", "technology", "engineering", "autonomous",
        "oc", "bc", "bcm", "mbc", "sc", "sca", "st",
        "cse", "cs", "ece", "eee", "it", "branch",
        "top", "best", "get", "will", "i", "can", "available", "possible",
    }

    words = [
        w for w in _norm(query).split()
        if len(w) > 2 and w not in stop
    ]

    return words
def has_college_intent(query: str) -> bool:
    q = _norm(query)

    intent_words = [
        "about",
        "abt",
        "think",
        "details",
        "detail",
        "college",
        "institute",
        "university"
    ]

    return any(word in q.split() for word in intent_words)

def search_college_details(query: str, limit: int = 10) -> list[str]:
    q = _norm(query)

    # Avoid using this for cutoff prediction queries
    if extract_cutoff_mark(query):
        return []
    if not has_college_intent(query):
        return []

    df = load_cutoff_df()

    df = df.dropna(subset=["College Name", "Code", "Branch"])
    df = df[df["college_norm"] != "nan"]

    filtered = df.copy()
    filtered["MATCH_SCORE"] = filtered["college_norm"].apply(
    lambda name: fuzz.partial_ratio(q, str(name))
)

    # Create score using fuzzy matching
    filtered["MATCH_SCORE"] = filtered["college_norm"].apply(
        lambda name: fuzz.partial_ratio(q, name)
    )

    filtered = filtered[filtered["MATCH_SCORE"] >= 65]

    if filtered.empty:
        return []

    filtered = filtered.sort_values("MATCH_SCORE", ascending=False)

    results = []

    for _, row in filtered.head(limit).iterrows():
        results.append(
            f"TNEA College Details\n"
            f"College Name: {row['College Name']}\n"
            f"TNEA Code: {row['Code']}\n"
            f"Branch: {row['Branch']}\n"
            f"OC Cutoff: {row.get('OC', 'N/A')}\n"
            f"BC Cutoff: {row.get('BC', 'N/A')}\n"
            f"BCM Cutoff: {row.get('BCM', 'N/A')}\n"
            f"MBC Cutoff: {row.get('MBC', 'N/A')}\n"
            f"SC Cutoff: {row.get('SC', 'N/A')}\n"
            f"SCA Cutoff: {row.get('SCA', 'N/A')}\n"
            f"ST Cutoff: {row.get('ST', 'N/A')}"
        )

    return results
def predict_colleges(query: str, limit: int = 10) -> list[str]:
    if not is_prediction_query(query):
        return []

    mark = extract_cutoff_mark(query)

    if mark is None:
        return []

    category = detect_category(query) or "OC"
    branch = detect_branch(query)

    df = load_cutoff_df()
    filtered = df.copy()
    location_words = get_location_filter_words(query)

    if location_words:
        pattern = "|".join(location_words)

        filtered = filtered[
            filtered["college_norm"].str.contains(pattern, na=False)
        ]

    if branch:
        branch_norm = _norm(branch)
        filtered = filtered[
            filtered["branch_norm"].str.contains(branch_norm, na=False)
        ]
    interest_branches = detect_interest_branches(query)

    if interest_branches:
        pattern = "|".join([_norm(b) for b in interest_branches])

        filtered = filtered[
            filtered["branch_norm"].str.contains(pattern, na=False)
        ]

    if category not in filtered.columns:
        return []

    filtered = filtered.copy()
    filtered["CUT_SORT"] = filtered[category].apply(clean_cutoff)

    filtered = filtered.dropna(subset=["CUT_SORT"])

    filtered = filtered[filtered["CUT_SORT"] <= mark]

    if filtered.empty:
        return []

    filtered = filtered.sort_values("CUT_SORT", ascending=False)

    results = []

    for _, row in filtered.head(limit).iterrows():
        results.append(
            f"TNEA College Prediction Based on Previous Year Cutoff\n"
            f"Your Cutoff: {mark}\n"
            f"Category Used: {category}\n"
            f"College Name: {row['College Name']}\n"
            f"TNEA Code: {row['Code']}\n"
            f"Branch: {row['Branch']}\n"
            f"Previous Year {category} Cutoff: {row[category]}\n"
            f"Note: This is only an approximate prediction based on previous year cutoff."
        )

    return results


def exact_cutoff_search(query: str) -> list[str]:
    if not is_cutoff_query(query):
        return []

    category = detect_category(query)
    branch = detect_branch(query)

    if not category and not branch:
        return []

    df = load_cutoff_df()
    filtered = df.copy()

    if branch:
        branch_norm = _norm(branch)
        filtered = filtered[
            filtered["branch_norm"].str.contains(branch_norm, na=False)
        ]

    college_words = extract_college_words(query)

    for word in college_words:
        temp = filtered[
            filtered["college_norm"].str.contains(word, na=False)
        ]

        if not temp.empty:
            filtered = temp

    if filtered.empty:
        return []

    if "OC" in filtered.columns:
        filtered = filtered.copy()
        filtered["OC_SORT"] = filtered["OC"].apply(clean_cutoff)

        q_words = set(_norm(query).split())

        if "top" in q_words or "best" in q_words:
            filtered = filtered.sort_values("OC_SORT", ascending=False)

    results = []

    for _, row in filtered.head(10).iterrows():
        if category:
            answer_line = f"{category} Cutoff Marks: {row.get(category, 'N/A')}"
        else:
            answer_line = " | ".join(
                [f"{c}: {row.get(c, 'N/A')}" for c in CATEGORIES]
            )

        results.append(
            f"TNEA Cutoff Data 2025\n"
            f"College Name: {row['College Name']}\n"
            f"TNEA Code: {row['Code']}\n"
            f"Branch: {row['Branch']}\n"
            f"{answer_line}"
        )

    return results


def embed_query(query: str, model: SentenceTransformer) -> np.ndarray:
    embedding = model.encode([query], convert_to_numpy=True)
    query_vector = np.asarray(embedding, dtype=np.float32)

    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    return query_vector


def faiss_search(query: str, top_k: int = TOP_K) -> list[str]:
    index, chunks = load_vector_store()

    print("[INFO] Loading embedding model for query...")
    model = SentenceTransformer(MODEL_NAME)

    query_vector = embed_query(query, model)
    distances, indices = index.search(query_vector, top_k)

    results = []

    print(f"\n[INFO] Top {top_k} retrieved chunks for: '{query}'")
    print("-" * 60)

    for rank, idx in enumerate(indices[0]):
        if idx == -1:
            continue

        chunk = chunks[idx]
        dist = distances[0][rank]

        print(f"[Rank {rank + 1}] Distance: {dist:.4f}")
        print(f"{chunk[:250]}...")
        print()

        results.append(chunk)

    return results


def search(query: str, top_k: int = TOP_K) -> list[str]:
    prediction_results = predict_colleges(query, limit=10)

    if prediction_results:
        print("[INFO] College prediction from Excel found.")

        for i, chunk in enumerate(prediction_results[:top_k], 1):
            print(f"[Prediction Rank {i}]\n{chunk}\n")

        return prediction_results[:top_k]

    exact_results = exact_cutoff_search(query)

    if exact_results:
        print("[INFO] Exact Excel cutoff match found.")

        for i, chunk in enumerate(exact_results[:top_k], 1):
            print(f"[Exact Rank {i}]\n{chunk}\n")

        return exact_results[:top_k]

    college_details = search_college_details(query, limit=10)

    if college_details:
        print("[INFO] College details from Excel found.")

        for i, chunk in enumerate(college_details[:top_k], 1):
            print(f"[College Rank {i}]\n{chunk}\n")

        return college_details[:top_k]

    return faiss_search(query, top_k)

def get_context(query: str, top_k: int = TOP_K) -> str:
    chunks = search(query, top_k)
    return "\n\n---\n\n".join(chunks)


if __name__ == "__main__":
    test_queries = [
        "What are the college will I get for 148.5 cut off",
        "What is the OC cutoff for CSE in PSG College of Technology?",
        "Top colleges for ECE in Coimbatore",
        "What is the eligibility criteria for TNEA 2026?",
        "What is the reservation percentage for MBC category?",
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        print(f"QUERY: {query}")
        print("=" * 60)

        context = get_context(query)

        print(f"\n[CONTEXT LENGTH]: {len(context)} characters")