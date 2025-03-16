import streamlit as st
import requests
from PIL import Image
import io
import streamlit.components.v1 as components

# API Endpoints
#UPLOAD_URL = "http://127.0.0.1:8000/upload/"
#AUDIO_UPLOAD_URL = "http://127.0.0.1:8000/upload_audio/"
#CHAT_URL = "http://127.0.0.1:8000/chat/"
UPLOAD_URL = "https://ecogenai-aircraft-predictive-maintenance.onrender.com/upload/"
AUDIO_UPLOAD_URL = "https://ecogenai-aircraft-predictive-maintenance.onrender.com/upload_audio/"
CHAT_URL = "https://ecogenai-aircraft-predictive-maintenance.onrender.com/chat/"


#RESULT_IMAGE_PATH = "./results/output.jpg"
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
            background-color: #0E1B30;
            color: white;
            border-radius: 6px;
            padding: 10px;
        }
        .sidebar .sidebar-content {
            background-color: #0E1B30;
            color: white;
        }
        h1, h2, h3, h4 {
            color: #00AEEF;
            text-align: center;
            animation: float 4s ease-in-out infinite;
        }
        .stFileUploader {
            border: 2px dashed #00AEEF;
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

# Streamlit App Layout
st.title("🚀 Predictive Maintenance AI")
st.markdown("Upload an image of your equipment and chat with AI for maintenance insights.")

# Layout with Two Columns: Image Upload & Chatbox
col1, col2 = st.columns([1, 1.2])

# 📌 Column 1: Image Upload and Prediction
with col1:
    st.subheader("📸 Upload Aircraft Image for Analysis")
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
                    #if annotated_image_url:
                        #st.image(RESULT_IMAGE_PATH, caption="🖼️ Predicted Image", use_container_width=True)
                    if annotated_image_url:
                        st.image(annotated_image_url, caption="🖼️ Predicted Image", use_container_width=True)

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

# 📌 Column 3: Audio Upload for Engine Sound
st.subheader("🎵 Upload Aircraft Engine Sound")
audio_file = st.file_uploader("Upload an MP3 file...", type=["mp3"])

if audio_file:
    with st.spinner("🔊 Processing audio..."):
        files = {"file": audio_file.getvalue()}
        response = requests.post(AUDIO_UPLOAD_URL, files=files)

        if response.status_code == 200:
            response_json = response.json()
            st.success(f"🔍 **Audio Analysis Result:** {response_json['message']}")
        else:
            st.error("❌ Error processing audio file!")
