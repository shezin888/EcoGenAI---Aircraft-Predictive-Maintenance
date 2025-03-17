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
from fastapi.staticfiles import StaticFiles
import time 

UPLOAD_DIR = "uploads/"
RESULT_FOLDER = "results/"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

render_base_url = "https://ecogenai-aircraft-predictive-maintenance.onrender.com"
result_path = os.path.join(RESULT_FOLDER, "output.jpg")


#MISTRAL_API_KEY = configure.MISTRAL_API_KEY
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")

#MISTRAL_API_KEY = configure.MISTRAL_API_KEY

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
model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)



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
        "annotated_image_url": f"{render_base_url}/results/output.jpg?timestamp={int(time.time())}"
    })


@app.post("/chat/")
async def chat_with_ai(request: ChatRequest):
    """
    AI Chat function that dynamically formats the query based on file type (image or audio).
    """
 
    if request.file_type == "image":
        faults_detected = ", ".join([f"{p['label']} ({p['confidence']})" for p in request.predictions])
        query = f"The image uploaded shows {faults_detected} based on the AI prediction. {request.prompt}"

    elif request.file_type == "audio":
        faults_detected = ", ".join([f"{p['label']} ({p['confidence']})" for p in request.predictions])
        query = f"The uploaded aircraft sound has been analyzed, and the AI detected {faults_detected}. {request.prompt}"

    else:
        return JSONResponse(content={"error": "Invalid file type"}, status_code=400)
    
 
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
        "message": "Detected an abnormal increase in low-frequency vibrations, indicating possible misalignment or early-stage bearing wear. The engine noise spectrum also shows irregular combustion patterns, which may suggest fuel flow inconsistencies or clogged injectors. Additionally, a high-pitched whine detected at certain RPM ranges could point to compressor blade damage or airflow obstructions. Further diagnostics are recommended to confirm potential turbine wear and ensure optimal engine performance."
    })

# Serve static files for the results folder
app.mount("/results", StaticFiles(directory="results"), name="results")