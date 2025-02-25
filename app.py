from flask import Flask, request, jsonify, render_template, send_file
import cv2
import numpy as np
import os
import supervision as sv
from inference import get_model

# Initialize Flask app
app = Flask(__name__)

# Load the model
MODEL_ID = "innovation-hangar-v2/1"
model = get_model(model_id=MODEL_ID)

# Upload folders
UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Function to clear old results before saving new ones
def clear_old_results():
    for file in os.listdir(RESULT_FOLDER):
        file_path = os.path.join(RESULT_FOLDER, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Clear previous result images
    clear_old_results()

    # Save the uploaded image
    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)

    # Read and process the image
    image = cv2.imread(image_path)

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
    annotated_image = bounding_box_annotator.annotate(
        scene=image, detections=detections)
    annotated_image = label_annotator.annotate(
        scene=annotated_image, detections=detections, labels=labels  # Use numbered labels
    )

    # Save the output image
    result_path = os.path.join(RESULT_FOLDER, "output.jpg")
    cv2.imwrite(result_path, annotated_image)

    return jsonify({
        "message": "Analysis complete!",
        "predictions": prediction_data,
        "annotated_image_url": "/results/output.jpg"
    })

@app.route("/results/output.jpg")
def get_annotated_image():
    return send_file(os.path.join(RESULT_FOLDER, "output.jpg"), mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(debug=True)
