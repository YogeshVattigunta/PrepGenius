import google.generativeai as genai
from IPython.display import clear_output, Markdown
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import easyocr
import numpy as np # Import numpy

from google.colab import files

genai.configure(api_key="AIzaSyCWzhzAqcvNgvR-qjtfhkewH6IcgxFxx7g")

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        return extracted_text

def questionor(notes, question_generator):
    question_generator = f"""
        You're a question-generating assistant.
    
        Steps:
        1. Analyze all the uploaded files.
        2. Understand the materials.
        3. Build 2 MCQ questions based on the materials
        3. Build 2 subjective questions based on the materials.
        4. Shuffle the questions, number them (e.g., Question 1:...), and
        5. separate each of the questions using <q> seprator.
        5. Output only the questions.
    
        Note: No markdown elements.
    """
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    material = extract_text_from_pdf(notes)
    
    questions = model.generate_content([question_generator, material]).text
    
    return questions.split("<q>")
    
def answers_sheet(questions, filename = "answer_sheet.txt"):
    answers = []

    for question in questions:
        print(question)
        answer = input("Answer: ")
        answers.append((f"Question : {question.strip()}", f"Answer : {answer.strip()}"))
    
    # Create a .txt file with the Q&A format
    with open(filename, "w") as file:
        for question, answer in answers:
            file.write(f"{question}\n{answer}\n\n")


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
    print(final_score)
    print()
    time_limit = input("Time left for Exam: ")
    
    
# Initialize EasyOCR
reader = easyocr.Reader(['en'])  # Add other languages if needed

def pdf_image_processor(pdf_path, output_path:str="previous year question paper.txt"):
    images = convert_from_path(pdf_path)

    for i, img in enumerate(images):
        print(f"Processing page {i + 1}...")
        # Convert PIL Image to NumPy array
        img_np = np.array(img)
        ocr_result = reader.readtext(img_np)  # Pass NumPy array to readtext
        page_text = "\n".join([text[1] for text in ocr_result])
        extracted_text += f"Page {i + 1}:\n{page_text}\n\n"

    return extracted_text


def important_topic_generator(pyq, notes, finial_score, time_left_for_exam):
    topics_template = f"""
    
        Your are a content generating assistant which tells user important topics to be covered within the time limit.
    
        Steps:
        1. You collects the study materials uploaded by the user: {notes}.
        2. You get the final socre of the quiz: {final_score}.
        3. You also collects previous year question paper: {pyq}.
        4. Then, analyze the question paper and the materials.
        5. After that you build most import topics to be covered within the time limit: {time_left_for_exam}
        6. Then, the questions are displayed in plain form.
    
    
        Note: don't display unnecessary text
        Note: no need of examples
    
    """
    
    model = genai.GenerativeModel(
        model_name = "gemini-1.5-pro",
        system_instruction=topics_template
    
    )
    
    response = model.generate_content(topics_template).text

    return response

