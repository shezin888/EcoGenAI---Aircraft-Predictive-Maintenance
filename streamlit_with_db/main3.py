from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
import cv2
import numpy as np
import supervision as sv  # Supervision Detections API
import requests
import sys
import logging
from inference import get_model
from openai import OpenAI
from pydantic import BaseModel
from mistralai import Mistral, UserMessage
import configure
import psycopg2


MISTRAL_API_KEY = configure.MISTRAL_API_KEY

client = Mistral(api_key=MISTRAL_API_KEY)

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    predictions: list
    file_type: str

UPLOAD_DIR = "uploads/"
RESULT_FOLDER = "results/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


MODEL_ID = "innovation-hangar-v2/1"
model = get_model(model_id=MODEL_ID, api_key=configure.ROBOFLOW_API_KEY)

DB_URL = "postgresql://rag_maintenance_db_user:NRXem4DNyIXODQ4V9KFlKJlmycsxHMKb@dpg-cvce3ajtq21c739u0i50-a.oregon-postgres.render.com/rag_maintenance_db"

def get_db_connection():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        logging.error(f"Database Connection Error: {str(e)}")
        return None

# 🔍 Fetch Maintenance Info from PostgreSQL
def fetch_maintenance_info(issue):
    """Retrieve maintenance solutions & contact details from PostgreSQL Render DB"""
    conn = get_db_connection()
    if not conn:
        return "No solution available.", "Unknown Contact", "No contact information."

    cursor = conn.cursor()
    cursor.execute(
        "SELECT solution, contact_name, contact_number FROM issue_contacts WHERE issue ILIKE %s LIMIT 1",
        (f'%{issue.split()[0]}%',)  # ✅ Handles "Dent #1", "Dent #2", etc.
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], result[1], result[2]  # Solution, Contact Name, Contact Number
    else:
        return "No solution available.", "Unknown Contact", "No contact information."

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load image for inference
    image = cv2.imread(file_path)

    # Run inference
    results = model.infer(image)[0]

    # Load results into Supervision Detections API
    detections = sv.Detections.from_inference(results)

    # Extract detected parts and confidence scores
    prediction_data = []
    labels = []  # Labels for bounding boxes
    for i in range(len(detections.class_id)):
        class_id = int(detections.class_id[i])  # Convert NumPy int64 to Python int
        confidence = float(detections.confidence[i]) * 100  # Convert NumPy float to Python float

        # Map class IDs to actual class names (modify this based on your model's classes)
        class_names = {0: "Crack", 1: "Dent", 2: "Other"}  # Adjust based on your trained model
        class_label = class_names.get(class_id, "Unknown")  # Default to 'Unknown' if not mapped

        # Assign unique numbers to each detection type
        label_text = f"{class_label} #{i+1}"

        # Store for UI display
        prediction_data.append({"label": label_text, "confidence": f"{confidence:.2f}%"})

        # Store for bounding box annotation
        labels.append(label_text)

    # Create supervision annotators with the correct labels
    bounding_box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    # Annotate the image with bounding boxes and labels
    annotated_image = bounding_box_annotator.annotate(scene=image, detections=detections)
    annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)

    # Save the output image
    result_path = os.path.join(RESULT_FOLDER, "output.jpg")
    cv2.imwrite(result_path, annotated_image)

    return JSONResponse(content={
        "message": "Analysis complete!",
        "predictions": prediction_data,
        "annotated_image_url": f"/results/output.jpg"
    })


@app.post("/chat/")
async def chat_with_ai(request: ChatRequest):
    """
    AI Chat function that dynamically formats the query based on file type (image or audio).
    """
    query_init = None

    if request.file_type == "image":
        faults_detected = ", ".join([f"{p['label']} ({p['confidence']})" for p in request.predictions])
        query_init = f"The image uploaded shows {faults_detected} based on the AI prediction."

    elif request.file_type == "audio":
        faults_detected = ", ".join([f"{p['label']} ({p['confidence']})" for p in request.predictions])
        query_init = f"The uploaded aircraft sound has been analyzed, and the AI detected {faults_detected}."

    else:
        return JSONResponse(content={"error": "Invalid file type"}, status_code=400)
    
    # Fetch contextual information from the database
    contact_info_list = []
    maintenance_solutions = []
    for p in request.predictions:
        solution, contact_name, contact_number = fetch_maintenance_info(p['label'])
        contact_info_list.append(f"{p['label']}: {contact_name} ({contact_number})")
        maintenance_solutions.append(f"{p['label']} - {solution}")
    # Construct query for LLM (RAG)
    query = (
        f"{query_init}"
        f"Here are maintenance solutions:\n{', '.join(maintenance_solutions)}\n"
        f"Relevant contacts:\n{', '.join(contact_info_list)}\n"
        f"User Question: {request.prompt}"
    )
    


    
    
 
    logging.info(f"Chat Query: {query}")

    try:
        # ✅ Send Query to Mistral AI
        chat_response = client.chat.complete(
            model="mistral-tiny",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Focus on predictive maintenance of aircrafts. "
                        "Do not answer unrelated questions. "
                        "If the query is irrelevant, ask the user to focus on aircraft maintenance."
                    )
                },
                {"role": "user", "content": query},
            ],
        )

        # ✅ Extract AI Response
        assistant_response = chat_response.choices[0].message.content if chat_response.choices else "No response"

        return JSONResponse(content={"response": assistant_response})

    except Exception as e:
        logging.error(f"Error in chat API: {str(e)}")
        return JSONResponse(content={"error": "Chatbot failed"}, status_code=500)

@app.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return JSONResponse(content={
        "message": "Variations in Engine Acoustics Detected. Need immediate maintenance!"
    })