import streamlit as st
import requests
from PIL import Image
import io

# API Endpoints
UPLOAD_URL = "http://127.0.0.1:8000/upload/"
CHAT_URL = "http://127.0.0.1:8000/chat/"
RESULT_IMAGE_PATH = "./results/output.jpg"
ROBOFLOW_API_URL = "https://api.roboflow.com"


# ✅ Ensure `st.set_page_config()` is the first Streamlit command
st.set_page_config(page_title="Predictive Maintenance AI", layout="wide")

# Custom CSS for a better UI experience
st.markdown("""
    <style>
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px;
        }
        .stTextArea > textarea {
            font-size: 16px;
        }
        .stTextInput > div > div > input {
            font-size: 16px;
        }
        .sidebar .sidebar-content {
            background-color: #1E1E1E;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Streamlit App Layout
st.title("🚀 Predictive Maintenance AI")
st.markdown("Upload an image of your equipment and chat with AI for maintenance insights.")

# Layout with Two Columns: Image Upload & Chatbox
col1, col2 = st.columns([1, 1.2])

# 📌 Column 1: Image Upload and Prediction
with col1:
    st.subheader("📸 Upload Equipment Image")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

    prediction_result = None
    annotated_image_url = None

    if uploaded_file:
        # Show image preview
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Upload Image to Backend
        with st.spinner("🛠️ Processing image..."):
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(UPLOAD_URL, files=files)

            if response.status_code == 200:
                response_json = response.json()
                prediction_result = response_json.get("predictions", [])
                annotated_image_url = response_json.get("annotated_image_url")
                if prediction_result:
                    detected_faults = "\n".join([f"✅ {p['label']} - {p['confidence']}" for p in prediction_result])
                    st.success(f"🔍 **Detected Faults:**\n{detected_faults}")

                    # Display Annotated Image (Bounding Boxes)
                    if annotated_image_url:
                        st.image(RESULT_IMAGE_PATH, caption="🖼️ Predicted Image", use_container_width=True)
                else:
                    st.warning("⚠️ No faults detected in the image.")
            else:
                st.error("❌ Error processing image!")

# 📌 Column 2: AI Chatbox (ONLY ENABLED AFTER PREDICTION)
with col2:
    st.subheader("💬 AI Chatbot - Get Maintenance Insights")

    if prediction_result:
        user_input = st.text_area("Ask a question about the detected issue:", placeholder="Type your question here...")

        if st.button("📝 Generate Report", key="chat_button"):
            with st.spinner("🤖 Fetching AI response..."):
                chat_payload = {
                    "prompt": user_input,
                    "predictions": prediction_result
                }
                response = requests.post(CHAT_URL, json=chat_payload)

            if response.status_code == 200:
                chat_response = response.json()

                print("Raw Chat API Response:", chat_response)  # Debugging

                st.markdown("### 🧠 AI Response")

                if "response" in chat_response:
                    st.info(chat_response["response"])
                else:
                    st.error("❌ AI response not available. Check server logs.")
 
