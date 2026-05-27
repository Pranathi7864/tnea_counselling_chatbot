from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_general_answer(query):
    prompt = f"""
You are a friendly TNEA counselling assistant.

The user message is not a TNEA-related question.

User Message:
{query}

Reply politely in 1-2 lines.
If the user asks your name, say:
"I am your TNEA counselling assistant."

Then guide them to ask about cutoff, colleges, eligibility, reservation, certificates, or counselling.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def generate_answer(query, context):
    prompt = f"""
You are a smart TNEA counselling advisor for Tamil Nadu engineering admission students.

Your role:
You should not simply summarize the retrieved context.
You should analyse the student's question and give useful counselling guidance.

Use the retrieved context only as factual support.

Rules:
1. Use ONLY the retrieved context for factual details like cutoff, courses, location, hostel, autonomy, NBA, intake, fees, and contact details.
2. Do not invent exact cutoff marks, courses, facilities, fees, or accreditation.
3. If the user asks "what do you think", "is it good", "review", "worth it", or "which is better",
   give a careful recommendation based on available facts.
4. If the context has irrelevant chunks, ignore them.
5. Do not list every raw course code unless the user asks for all courses.
6. Explain in simple student-friendly English.
7. If exact data is missing, say "Based on the available information..."
8. If the answer is based on previous year cutoff, clearly say:
   "This is only an approximate prediction based on previous year cutoff."

For college opinion/advice questions, structure the answer like this:

- Short opinion
- Why it may be a good choice
- Things to check before choosing
- Best suited for which students
- Final suggestion

User Question:
{query}

Retrieved Context:
{context}

Final Answer:
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            return f"""
Gemini API quota/rate limit reached.

Here is the retrieved TNEA information directly from your documents:

{context[:2500]}

Note: This answer is from retrieved context only. Gemini formatting was skipped.
"""

        return f"""
Gemini API is not working now.

Reason:
{e}

Here is the retrieved context directly:

{context[:2500]}
"""