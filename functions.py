import google.generativeai as genai
import PyPDF2
import numpy as np # Import numpy
import time


def stream_data(text:str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)



def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        return extracted_text

def questionor(notes):
    question_generator = f"""
        You're a question-generating assistant.

        Steps:
        1. Analyze all the uploaded files.
        2. Understand the materials.
        3. Build 2 MCQ questions based on the materials.
        4. Build 2 subjective questions based on the materials.
        5. Shuffle the questions, number them (e.g., Question 1:...), and
        6. separate each of the questions using <q> separator.
        7. Output only the questions.

        Note: No markdown elements.
    """

    # Initialize the model
    genai.configure(api_key="AIzaSyCNd7y_kcAjV9z817CXc9mJSAAehPHJqzM")
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Extract text from the uploaded notes (assumed PDF)
    material = extract_text_from_pdf(notes)

    # Generate questions using the model
    questions = model.generate_content([question_generator, material]).text

    # Split the questions using the <q> separator
    question_list = questions.split("<q>")
    return question_list

def evaluator(answer_paper):

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


    answer_sheet = genai.upload_file(answer_paper)
    model = genai.GenerativeModel("gemini-1.5-pro")
    evaluation = model.generate_content([evaluator, answer_sheet]).text

    final_score = evaluation.split("<evl>")[-1]
    return final_score



def important_topic_generator(pyq, notes, final_score, time_left_for_exam):

    topics_template = f"""

        Your are a content generating assistant which tells user important topics to be covered within the time limit.

        Steps:
        1. You collects the study materials uploaded by the user: {notes}.
        2. You get the final socre of the quiz: {final_score}.
        3. You also collects previous year question paper: {pyq}.
        4. Then, analyze the question paper and the materials.
        5. After that you build most import topics to be covered within the time limit: {time_left_for_exam}
        6. Then, those import points will be displayed in .


        Note: don't display unnecessary text
        Note: no need of examples

    """
    genai.configure(api_key="AIzaSyBrEyFwfl2uy_EHO4oC2EqPI5AukkJI7cw")
    model = genai.GenerativeModel(
        model_name = "gemini-1.5-pro",
        system_instruction=topics_template

    )

    response = model.generate_content(topics_template).text

    return response

