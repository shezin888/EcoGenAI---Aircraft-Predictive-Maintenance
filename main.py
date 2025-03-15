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

render_base_url = "https://ecogenai-aircraft-predictive-maintenance.onrender.com"
result_path = os.path.join(RESULT_FOLDER, "output.jpg")

#MISTRAL_API_KEY = configure.MISTRAL_API_KEY
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")


client = Mistral(api_key=MISTRAL_API_KEY)

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    predictions: list

UPLOAD_DIR = "uploads/"
RESULT_FOLDER = "results/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

MODEL_ID = "innovation-hangar-v2/1"
model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)

#model = get_model(model_id=MODEL_ID, api_key=configure.ROBOFLOW_API_KEY)


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
        "annotated_image_url": f"{render_base_url}/results/output.jpg"
    })


@app.post("/chat/")
async def chat_with_ai(request: ChatRequest):
    faults_detected = ", ".join([f"{p['label']} ({p['confidence']})" for p in request.predictions])

    query = f"The image uploaded shows {faults_detected} based on the AI prediction. {request.prompt}"
    logging.info(f"Chat Query: {query}")

    try:
        # Send Request to Mistral AI
       
       chat_response = client.chat.complete(
                        model="mistral-tiny",
                        messages=[
                    {
                       "role": "system", "content": "Focus on predictive maintenance on aircrafts. Don't answer any unrelated questions and any questions unrelated to the predictive maintenance or maintenance of aircraft should be redirected to tell the user to ask relevant questions"},
                          {"role": "user", "content": query},
        ],
                        )

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
        "message": "Engine Lubrication low and need maintenance"
    })
