# EcoGenAI - Aircraft Predictive Maintenance 

**EcoGenAI** is an AI-powered predictive maintenance platform for the aerospace industry. It combines **computer vision**, **large language models (LLMs)**, and **GAN-based acoustic analysis** to detect fuselage defects, analyze engine sounds, and provide intelligent maintenance recommendations - all through an interactive web interface.  

---

## 🚀 Running the Application Locally  

### 1️⃣ Install Dependencies  
Run the following command to install all required dependencies:  
```bash
pip install -r requirements.txt
```
   - Ensure that you include both **Mistral** and **Roboflow** API keys in the `configure.py` file before running the application.

### 2️⃣ Start the Backend (FastAPI Server)  
 ```bash
   python -m uvicorn main:app --reload
   ```

### 3️⃣ Start the Frontend (Streamlit Server)
   ```bash
   python -m streamlit run app.py
   ```
---

## 🎯 Features
- Fuselage Fault Detection (OpenCV2 + Roboflow)
- LLM-Powered Maintenance Assistant (OpenHermes Mistral)
- GAN-Based Acoustic Engine Fault Detection (in progress)
- Interactive, user-friendly Streamlit UI

---

## 🧠 GAN Architecture on Acoustic Data
The GAN model is trained on normal engine sound data to generate synthetic faulty sound samples,
enabling robust fault detection even when real-world failure data is scarce.

![alt text](https://github.com/shezin888/EcoGenAI---Aircraft-Predictive-Maintenance/blob/master/GAN.drawio.png)
