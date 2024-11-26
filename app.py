from flask import Flask, render_template, request, redirect, url_for
import os
import google.generativeai as genai

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
genai.configure(api_key="AIzaSyDGch-1IdXfW6o9q6-dMwIXBV17FNv6CJA")  # Replace with your actual API key

# Helper function to generate questions using Gemini model
def generate_questions(pdf_path):
    try:
        files = genai.upload_file(pdf_path)
        question_generator = """
        You are a question-generating assistant. 

        Steps:
        1. Analyze all the uploaded files.
        2. Understand the materials.
        3. Build 2 MCQ questions based on the provided materials.
        4. Build 2 subjective questions based on the provided materials.
        5. Shuffle the MCQ and subjective questions, add the question number (e.g: Question 1:...., Question 2:...) and display it.
        6. Add a unique separator <q> to separate each question.

        Note: Only the questions are required, no need for any other text.
        Note: No need to add markdown elements.
        Note: Total number of questions should be 4.
        """
        model = genai.GenerativeModel("gemini-1.5-pro")
        questions = model.generate_content([question_generator, files]).text
        return questions.split("<q>")
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []  # Return an empty list on error

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as txt_file:
        extracted_text = txt_file.read()
    return extracted_text

def evaluation(answer_sheet):
    evaluator = """
        You are an evaluation assistant where:

        1. You get the answer sheet provided by the user.
        2. You check answers corresponding to the questions.
        3. Evaluate the answers with questions.
        4. Add evaluation as: correct or wrong.
        5. Display the evaluation as: evaluation: correct.
        6. Convert the evaluation score into a percentage and display it at the end as "Total score: ".
        7. Add a unique separator <evl> between the last question and Total score.
    """

    Q_and_A_sheet = extract_text_from_txt(answer_sheet)

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        result = model.generate_content([evaluator, Q_and_A_sheet]).text
        print(result)
        final_score = result.split("<evl>")[-1]  # Corrected from 'evaluation' to 'result'
        return final_score
    except Exception as e:
        print(f"Error during evaluation: {e}")
        return "Evaluation failed."

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
            if not GENERATED_QUESTIONS:
                return render_template('error.html', message="Failed to generate questions. Please try again.")
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
            f.write(f"Answer {i}: {answer}\n\n")

    # Perform evaluation of the answers
    evaluation_result = evaluation(answer_file)

    return render_template('evaluation.html', evaluation_result=evaluation_result)

if __name__ == '__main__':
    app.run(debug=True)  # Set debug=False in production

    # Function to generate a study timeline based on grade
def generate_study_timeline(grade):
    timeline_request = f"""
    Create a study timeline for a student with grade '{grade}'. 
    Include specific topics to study each week for the next month.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        timeline = model.generate_content([timeline_request]).text
        return timeline.split("\n")  # Assuming timeline items are separated by new lines
    except Exception as e:
        print(f"Error generating timeline: {e}")
        return []  # Return an empty list on error

# Modify the evaluate route to include study timeline
@app.route('/evaluate', methods=['POST'])
def evaluate():
    answer_sheet = request.json.get('answer_sheet')
    final_score = calculate_score(answer_sheet)  # Placeholder for actual scoring logic
    grade = assess_performance(final_score)  # Assess performance based on the score
    study_topics = fetch_study_topics(grade)  # Fetch study topics based on the grade
    study_timeline = generate_study_timeline(grade)  # Generate study timeline based on the grade
    return jsonify({
        'final_score': final_score,
        'grade': grade,
        'study_topics': study_topics,
        'study_timeline': study_timeline  # Include the study timeline in the response
    })