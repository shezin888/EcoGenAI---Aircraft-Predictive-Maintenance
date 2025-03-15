# EcoGenAI Web Application

## Steps to run the application locally

1. Run the `requirements.txt` file to install all the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   - Ensure that you include both **Mistral** and **Roboflow** API keys in the `configure.py` file before running the application.

2. Start the FastAPI server using the command:
   ```bash
   python -m uvicorn main:app --reload
   ```

3. Start the Streamlit server using the command:
   ```bash
   python -m streamlit run app.py
   
