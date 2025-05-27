# Install necessary packages
!pip install --quiet langchain llama-index openai tiktoken faiss-cpu PyPDF2
!pip install -q langchain-community langchainhub python-dotenv gradio

import os
from dotenv import load_dotenv
import openai
import gradio as gr
import PyPDF2

load_dotenv()

# Initialize OpenAI client properly
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global variable to store extracted resume text
current_resume_text = ""

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def process_resume(pdf_file):
    """Process the uploaded resume"""
    global current_resume_text

    if not pdf_file:
        return "Please upload a PDF file."

    try:
        current_resume_text = extract_text_from_pdf(pdf_file)
        if not current_resume_text:
            return "No text found in PDF. Please try another file."
        return f"✅ Resume processed! Ready for questions."
    except Exception as e:
        current_resume_text = ""
        return f"❌ Error: {str(e)}"

def answer_question(question, chat_history):
    """Answer questions about the resume"""
    global current_resume_text

    if not current_resume_text:
        response = "Please upload a resume first."
        chat_history.append([question, response])
        return chat_history, ""

    if not question.strip():
        return chat_history, ""

    try:
        prompt = f"""
        Based on this resume, answer the question:

        Resume: {current_resume_text}

        Question: {question}

        Answer clearly and concisely based only on the resume content.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )

        answer = response.choices[0].message.content
        chat_history.append([question, answer])
        return chat_history, ""

    except Exception as e:
        response = f"Error: {str(e)}"
        chat_history.append([question, response])
        return chat_history, ""

# Simple custom CSS
css = """
.gradio-container {
    background: linear-gradient(135deg, #74b9ff, #0984e3);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.main-title {
    color: white;
    text-align: center;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.container {
    background: white;
    border-radius: 15px;
    padding: 2rem;
    margin: 1rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.btn-primary {
    background: #0984e3 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 600 !important;
}

.btn-secondary {
    background: #636e72 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
}

.sample-questions {
    background: #e8f4f8;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.question-item {
    color: #2d3436;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}
"""

# Create the interface
with gr.Blocks(css=css, title="Resume Q&A") as demo:

    gr.HTML('<h1 class="main-title">📋 Resume Q&A Assistant</h1>')

    with gr.Row():
        # Left side - Upload
        with gr.Column(scale=1, elem_classes="container"):
            gr.Markdown("### 📄 Upload Resume")

            pdf_input = gr.File(
                label="Choose PDF file",
                file_types=[".pdf"]
            )

            process_btn = gr.Button(
                "Process Resume",
                variant="primary",
                elem_classes="btn-primary"
            )

            status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2
            )

            # Sample questions
            gr.HTML("""
            <div class="sample-questions">
                <h4>💡 Try asking:</h4>
                <div class="question-item">• What skills does this person have?</div>
                <div class="question-item">• How many years of experience?</div>
                <div class="question-item">• What is their education?</div>
                <div class="question-item">• What was their last job?</div>
                <div class="question-item">• Rate this resume 1-10</div>
            </div>
            """)

        # Right side - Chat
        with gr.Column(scale=2, elem_classes="container"):
            gr.Markdown("### 💬 Ask Questions")

            chatbot = gr.Chatbot(
                height=400,
                label="Chat"
            )

            with gr.Row():
                question = gr.Textbox(
                    placeholder="Ask something about the resume...",
                    label="Your question",
                    scale=4
                )
                ask_btn = gr.Button(
                    "Ask",
                    scale=1,
                    variant="primary",
                    elem_classes="btn-primary"
                )

            clear_btn = gr.Button(
                "Clear Chat",
                elem_classes="btn-secondary"
            )

    # Event handlers
    process_btn.click(
        process_resume,
        inputs=[pdf_input],
        outputs=[status]
    )

    ask_btn.click(
        answer_question,
        inputs=[question, chatbot],
        outputs=[chatbot, question]
    )

    question.submit(
        answer_question,
        inputs=[question, chatbot],
        outputs=[chatbot, question]
    )

    clear_btn.click(
        lambda: [],
        outputs=[chatbot]
    )

if __name__ == "__main__":
    print("Starting Resume Q&A Assistant...")
    demo.launch()
