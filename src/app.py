import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add src folder to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(CURRENT_DIR)

from generator import ask_tnea_bot

app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_DIR, "templates"),
    static_folder=os.path.join(PROJECT_DIR, "static")
)

CORS(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "success": False,
                "answer": "Please type a question."
            })

        answer = ask_tnea_bot(question)

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "answer": f"Something went wrong: {str(e)}"
        })


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)