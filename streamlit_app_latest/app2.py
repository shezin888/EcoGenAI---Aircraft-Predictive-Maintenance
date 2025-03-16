import streamlit as st
import requests
from PIL import Image
import io
import streamlit.components.v1 as components

# API Endpoints
UPLOAD_URL = "http://127.0.0.1:8000/upload/"
AUDIO_UPLOAD_URL = "http://127.0.0.1:8000/upload_audio/"
CHAT_URL = "http://127.0.0.1:8000/chat/"
RESULT_IMAGE_PATH = "./results/output.jpg"
ROBOFLOW_API_URL = "https://api.roboflow.com"


# ✅ Ensure `st.set_page_config()` is the first Streamlit command
st.set_page_config(page_title="✈️ EcoGenAI - AI for Aircraft Maintenance", layout="wide")

# Injecting the Particles.js script for live animated background
components.html("""
    <div id="particles-js" style="position:fixed; width:100%; height:100vh; z-index:-1;"></div>
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <script>
        particlesJS("particles-js", {
            "particles": {
                "number": {"value": 80, "density": {"enable": true, "value_area": 800}},
                "color": {"value": "#00AEEF"},
                "shape": {"type": "circle"},
                "opacity": {"value": 0.5},
                "size": {"value": 3, "random": true},
                "move": {"enable": true, "speed": 2, "direction": "none"}
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {"onhover": {"enable": true, "mode": "repulse"}}
            },
            "retina_detect": true
        });
    </script>
""", height=0)

# Enhanced Custom CSS for animations
st.markdown("""
    <style>
        body {
            background-color: #1A2B44;
            color: white;
            font-family: 'Arial', sans-serif;
        }
        .stApp {
            background: linear-gradient(to right, #001F3F, #0074D9);
            color: white;
            padding: 20px;
        }
        .stButton > button {
            background: #0074D9;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px;
            border: none;
            transition: 0.3s;
            animation: pulse 2s infinite alternate;
        }
        .stButton > button:hover {
            background: #00AEEF;
        }
        .stTextArea > textarea, .stTextInput > div > div > input {
            font-size: 16px;
            background-color: #fcfcfc;
            color: white;
            border-radius: 6px;
            padding: 10px;
        }
        .sidebar .sidebar-content {
            background-color: #fcfcfc;
            color: white;
        }
        h1, h2, h3, h4 {
            color: #fcfcfc;
            text-align: center;
            animation: float 4s ease-in-out infinite;
        }
        .stFileUploader {
            border: 2px dashed #fcfcfc;
            padding: 15px;
            border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.1);
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 5px rgba(0, 174, 239, 0.3); }
            50% { box-shadow: 0 0 20px rgba(0, 174, 239, 0.8); }
            100% { box-shadow: 0 0 5px rgba(0, 174, 239, 0.3); }
        }
    </style>
""", unsafe_allow_html=True)

# Add Particles.js for animated background
st.markdown("""
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <div id="particles-js" style="position:fixed; width:100%; height:100vh; z-index:-1;"></div>
    <script>
        particlesJS("particles-js", {
            "particles": {
                "number": { "value": 80, "density": {"enable": true, "value_area": 800} },
                "color": { "value": "#00AEEF" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5 },
                "size": { "value": 3, "random": true },
                "move": { "enable": true, "speed": 2, "direction": "none" }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": { "onhover": {"enable": true, "mode": "repulse"} }
            },
            "retina_detect": true
        });
    </script>
""", unsafe_allow_html=True)


# Streamlit App Layout
st.markdown("""
# ✈️ EcoGenAI - AI-Powered Aircraft Maintenance
""", unsafe_allow_html=True)

st.markdown("""
EcoGenAI is an advanced AI and LLM-powered platform designed specifically for the aircraft industry. It helps engineers, technicians, and aviation experts analyze aircraft images, detect faults, and get AI-driven maintenance advice. Users can upload images to detect issues, chat with the AI for expert guidance, and even analyze aircraft engine sounds to identify potential anomalies, making it a comprehensive solution for predictive maintenance.
""")



st.markdown("Upload an **image** or **aircraft engine sound**, and chat with AI for maintenance insights.")

# Layout with Two Columns: Image & Audio Upload in Column 1, AI Chat in Column 2
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🛠️ Upload Aircraft Image OR Engine Sound")

    # ✅ Unified Upload Box in First Column
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📷 Upload Image or 🎵 Upload Audio", type=["jpg", "png", "jpeg", "mp3"])
    st.markdown('</div>', unsafe_allow_html=True)  # Close the upload box

    # ✅ Variables to Hold Processing Results
    image_predictions = None
    audio_predictions = None
    annotated_image_url = None

    # 📌 Ensure the Correct AI Processing Based on File Type
    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        # ✅ If Image is Uploaded
        if file_extension in ["jpg", "jpeg", "png"]:
            st.image(Image.open(uploaded_file), caption="Uploaded Image", use_container_width=True)

            with st.spinner("🛠️ Processing image..."):
                files = {"file": uploaded_file.getvalue()}
                response = requests.post("http://127.0.0.1:8000/upload/", files=files)

                if response.status_code == 200:
                    response_json = response.json()
                    image_predictions = response_json.get("predictions", [])
                    annotated_image_url = response_json.get("annotated_image_url")
                else:
                    st.error("❌ Error processing image!")

        # ✅ If Audio is Uploaded
        elif file_extension == "mp3":
            with st.spinner("🔊 Processing audio..."):
                files = {"file": ("audio.mp3", uploaded_file.getvalue(), "audio/mpeg")}
                response = requests.post("http://127.0.0.1:8000/upload_audio/", files=files)

                if response.status_code == 200:
                    response_json = response.json()
                    audio_predictions = response_json.get("predictions", [])
                else:
                    st.error("❌ Error processing audio file!")

    # ✅ Show "Prediction Results" ONLY AFTER processing is done
    if image_predictions is not None or audio_predictions is not None:
        st.markdown("---")  # Horizontal Line for Separation
        st.subheader("📊 Prediction Results")

        # ✅ Display Image Predictions
        if image_predictions is not None:
            detected_faults = "\n".join([f"✅ {p['label']} - {p['confidence']}" for p in image_predictions])
            st.success(f"🔍 **Detected Faults (Image):**\n{detected_faults}")

            if annotated_image_url:
                st.image("./results/output.jpg", caption="🖼️ Predicted Image", use_container_width=True)

        # ✅ Display Audio Predictions
        elif audio_predictions is not None:
            st.success(f"🔍 **Audio Analysis Result:** {response_json['message']}")

# 📌 AI Chatbox in Second Column
with col2:
    # ✅ AI Chat for Image Predictions
    if image_predictions is not None and audio_predictions is None:
        st.subheader("📷 AI Chat for Image Faults")
        user_input_image = st.text_area("Ask about image-based faults:", key="image_chat")

        if st.button("📝 Get Image Report", key="image_report_button"):
            with st.spinner("🤖 Fetching AI response..."):
                chat_payload = {"prompt": user_input_image, "predictions": image_predictions, "file_type": "image"}
               
                response = requests.post("http://127.0.0.1:8000/chat/", json=chat_payload)

            if response.status_code == 200:
                chat_response = response.json()
                st.markdown("### 🧠 AI Response (Image)")
                st.info(chat_response.get("response", "No response available."))
            else:
                st.error("❌ AI response not available. Check server logs.")

    # ✅ AI Chat for Audio Predictions
    elif audio_predictions is not None and image_predictions is None:
        st.subheader("🎵 AI Chat for Audio Anomalies")
        user_input_audio = st.text_area("Ask about engine sound issues:", key="audio_chat")

        if st.button("📝 Get Audio Report", key="audio_report_button"):
            with st.spinner("🤖 Fetching AI response..."):
                chat_payload = {"prompt": user_input_audio, "predictions": audio_predictions, "file_type": "audio"}
                
                response = requests.post("http://127.0.0.1:8000/chat/", json=chat_payload)

            if response.status_code == 200:
                chat_response = response.json()
                st.markdown("### 🧠 AI Response (Audio)")
                st.info(chat_response.get("response", "No response available."))
            else:
                st.error("❌ AI response not available. Check server logs.")

    elif image_predictions is None and audio_predictions is None:
        st.warning("⚠️ Upload an image or an audio file to enable AI chat.")
