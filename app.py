from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import google.generativeai as genai
import PyPDF2

# Set up Flask app
app = Flask(__name__)

# Path to store uploaded files
MATERIALS = 'Materials'
if not os.path.exists(MATERIALS):
    os.makedirs(MATERIALS)

ANSWERS = "answer_sheet"
if not os.path.exists(ANSWERS):
    os.makedirs(ANSWERS)

# Store questions in a global variable (ideally, use a session or database in production)
GENERATED_QUESTIONS = []

# Configure API key for Gemini
genai.configure(api_key="AIzaSyCNd7y_kcAjV9z817CXc9mJSAAehPHJqzM")

# Helper function to generate questions using Gemini model
def generate_questions(pdf_path):
    files = genai.upload_file(pdf_path)
    question_generator = """
    Your a question generating assistant. 

    Steps:
    1. You analyze all the uploaded files
    2. You understand the materials
    3. After that you have to build 2 MCQ questions based on the provided materials
    4. Then, build 2 subjective questions based on the provided materials.
    5. After that you will shuffle the MCQ and subjective questions, add the question number (e.g: Question 1:...., Question 2:...) and display it.
    6. You will then add a unique separator <q> to separate each question.

    Note: only the questions are required, no need of any other text.
    Note: No need to add markdown element.
    Note: Total No question should be 4.
    """
    model = genai.GenerativeModel("gemini-1.5-pro")
    questions = model.generate_content([question_generator, files]).text
    return questions.split("<q>")

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as txt_file:
        extracted_text = txt_file.read()
    return extracted_text


def evaluation(answer_sheet):

    evaluator = """
        Your are an evaluation assistant where:

        1. You get the answer sheet provided by the user.
        2. You check Answers corresponding to the question.
        3. Then, evaluate the answers with questions.
        4. And add evaluation as : correct, worng
        5. The evaluation will be displayed as, evaluation: correct
        6. The convert the evaluation score into percentage and display it at the end as "Total score : "
        7. The you will add a unique seprator <evl> between the last question and Total score

        example:
            Question 1: What is the capital of France?
            Answer 1: Paris
            Evaluation 1: correct
            Question 2: What is the largest planet in our solar system?
            Answer 2: Sun
            Evaluation 2: wrong


    """

    Q_and_A_sheet = extract_text_from_txt(answer_sheet)



    model = genai.GenerativeModel("gemini-1.5-pro")
    result = model.generate_content([evaluator, Q_and_A_sheet]).text
    print(result)
    final_score = evaluation.split("<evl>")[-1]
    return final_score



# Flask route to upload file
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global GENERATED_QUESTIONS  # Store questions globally
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(MATERIALS, file.filename)
            file.save(filepath)
            GENERATED_QUESTIONS = generate_questions(filepath)
            return render_template('questions.html', questions=GENERATED_QUESTIONS, file_path=filepath)
    return render_template('upload.html')



# Flask route to submit answers
@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    global GENERATED_QUESTIONS  # Access generated questions
    answer_sheet_folder = 'answer_sheet'
    if not os.path.exists(answer_sheet_folder):
        os.makedirs(answer_sheet_folder)

    # Retrieve answers from the form
    answers = []
    for key in request.form.keys():
        answers.append(request.form[key])

    # Save the questions and answers to a file
    answer_file = os.path.join(answer_sheet_folder, 'answersheet.txt')
    with open(answer_file, 'w') as f:
        for i, (question, answer) in enumerate(zip(GENERATED_QUESTIONS, answers), start=1):
            f.write(f"{question}\n")
            f.write(f"Answer {i}: {answer}\n")

    # Evaluate answers
    final_score = evaluation(answer_file)
    
    return render_template('score.html', final_score=final_score)

# Route to view the final score
@app.route('/score')
def view_score():
    return render_template('score.html')

if __name__ == '__main__':
    app.run(debug=True)
