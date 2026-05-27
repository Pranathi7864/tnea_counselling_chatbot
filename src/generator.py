from retriever import get_context
from gemini_answer import generate_answer, generate_general_answer


def is_only_greeting(query):
    q = query.lower().strip()

    greetings = [
        "hi",
        "hello",
        "hey",
        "hii",
        "hai",
        "hi bro",
        "hello bro",
        "hey bro"
    ]

    return q in greetings


def is_tnea_related(query):
    q = query.lower()

    tnea_keywords = [
        "tnea",
        "counselling",
        "counseling",
        "cutoff",
        "cut off",
        "college",
        "colleges",
        "engineering",
        "branch",
        "course",
        "rank",
        "marks",
        "oc",
        "good",
"better",
"best",
"think",
"about",
"abt",
"review",
"opinion",
"worth",
        "bc",
        "bcm",
        "mbc",
        "sc",
        "sca",
        "st",
        "reservation",
        "eligibility",
        "certificate",
        "allotment",
        "choice filling",
        "admission",
        "anna university",
        "coimbatore",
        "chennai",
        "madurai",
        "salem",
        "trichy",
        "tirupur",
        "erode"
    ]

    return any(word in q for word in tnea_keywords)


def ask_tnea_bot(query):
    if is_only_greeting(query):
        return (
            "Hello! I am your TNEA counselling assistant. "
            "I can help with cutoff prediction, college details, eligibility, "
            "reservation, certificates, and counselling process."
        )

    if not is_tnea_related(query):
        return generate_general_answer(query)

    context = get_context(query)

    if not context.strip():
        return "Sorry, I could not find enough information in the documents."

    answer = generate_answer(query, context)
    return answer


if __name__ == "__main__":
    print("=" * 60)
    print("TNEA Counselling RAG Assistant")
    print("Type 'exit' to stop")
    print("=" * 60)

    while True:
        query = input("\nAsk your TNEA question: ")

        if query.lower().strip() in ["exit", "quit"]:
            print("Thank you!")
            break

        answer = ask_tnea_bot(query)

        print("\nAnswer:")
        print(answer)