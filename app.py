import streamlit as st
import numpy as np
import google.generativeai as genai
import os
from pdf2image import convert_from_path
import easyocr
from functions import questionor, evaluator, important_topic_generator, stream_data, extract_text_from_pdf

def pdf_image_processor(pdf_path):
    try:
        reader = easyocr.Reader(['en'])
        extracted_text = ""  # Initialize extracted_text
        
        # Check if path is directory or file
        if os.path.isdir(pdf_path):
            pdf_files = [f for f in os.listdir(pdf_path) if f.endswith('.pdf')]
            if not pdf_files:
                return "No PDF files found in directory"
            pdf_path = os.path.join(pdf_path, pdf_files[0])
        
        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path)
        except Exception as e:
            return f"Error converting PDF: Make sure Poppler is installed. Error: {str(e)}"

        for i, img in enumerate(images):
            print(f"Processing page {i + 1}...")
            img_np = np.array(img)
            ocr_result = reader.readtext(img_np)
            page_text = "\n".join([text[1] for text in ocr_result])
            extracted_text += f"Page {i + 1}:\n{page_text}\n\n"

        return extracted_text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"



tab1, tab2, tab3 = st.tabs(["Assisment", "Dashboard", "Chatbot"])


with tab1:
    if 'step' not in st.session_state:
        st.session_state.step = 1

    if st.session_state.step == 1:
        uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
        upload_button = st.button("Upload")
        if uploaded_file is not None:
            if upload_button:
                # Save file to Materials folder
                if not os.path.exists("Materials"):
                    os.makedirs("Materials")
                    
                file_path = os.path.join("Materials", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        # Initialize answers in session state if not exists
        if 'quiz_answers' not in st.session_state:
            st.session_state.quiz_answers = {}

        # Generate and display quiz
        notes = [f for f in os.listdir("Materials") if f.endswith('.pdf')]
        # Store questions in session state if not exists
        if 'questions' not in st.session_state:
            st.session_state.questions = questionor(notes=os.path.join("Materials", notes[0]))

        # Display questions and collect answers
        for q in st.session_state.questions:
            st.write(q)
            # Use the stored answer as default value if it exists
            answer = st.text_input("Your answer:", key=f"answer_{q}", 
                                 value=st.session_state.quiz_answers.get(q, ""))
            # Store answer in session state
            st.session_state.quiz_answers[q] = answer

        if st.button("Submit"):
            with open("answer_sheet/answer_sheet.txt", "w") as file:
                for question, answer in st.session_state.quiz_answers.items():
                    file.write(f"{question}\n{answer}\n\n")
            st.session_state.step = 3
            st.rerun()
 
    elif st.session_state.step == 3:
        sheet = [f for f in os.listdir("Answer_sheet") if f.endswith('.txt')]

        evaluation = evaluator(answer_paper=os.path.join("Answer_sheet",sheet[0]))
        st.write(evaluation)
        time_left = st.number_input("Time left for exam:", min_value=0, max_value=168)
        submit_button = st.button("Submit", key="time left")
        if submit_button:
            # Store submit button state in session state
            st.session_state.submitted = True
            st.success("You have sucessfully completed the assisment, you can now go to Dashboard")


with tab2:
    # Check submission state from session state instead of submit_button directly
    if st.session_state.get('submitted', False):
        pyq = pdf_image_processor(pdf_path="PQA")
        notes = extract_text_from_pdf(
            pdf_path=[f for f in os.listdir("Materials") if f.endswith('.pdf')]
        )
        
        time_schedule = important_topic_generator(
            pyq=pyq,
            notes=notes,
            time_left_for_exam=time_left,
            final_score=evaluation
        )
        st.markdown(time_schedule)



with tab3:
    def chatbot(material:str, user_prompt:str):
        chat_template = f"""
        
            You are a doubt clearing assistant, You clear students doubts based on the materials provided. 

            Steps to follow:
            1. Get the materials: {material}
            2. Andget the user prompt: {user_prompt}
            3. Analyze the user prompt and get the realevent data from the material
            4. Display it accordingly.

        """
        genai.configure(api_key="AIzaSyA91xTtkqWCkl6I8nOY6KkaVocm4JlnTj8")
        model = genai.GenerativeModel(
            model_name = "gemini-1.5-pro",
            system_instruction = chat_template
            )
        # generated_text = model.generate_content(user_prompt)
        chat = model.start_chat(
                history=[
                    {"role": "user", "parts": user_prompt},
                    {"role": "model", "parts": chat_template},
                ]
        )
        response = chat.send_message(user_prompt)
        text = response.text
        return text

    prompt = st.chat_input("What is your doubt")
    notes = extract_text_from_pdf(pdf_path=[f for f in os.listdir("Materials") if f.endswith('.pdf')])
    if prompt:
        text_gen = chatbot(material=notes, user_prompt=prompt)

        text_flow = stream_data(text_gen)
        st.write_stream(text_flow)
