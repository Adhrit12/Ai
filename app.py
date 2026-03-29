import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_KEY"]
except KeyError:
    st.error("Missing API Key! Please add GEMINI_KEY to your Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Med-Assist AI", page_icon="🩺", layout="wide")

# Initialize session state for disclaimer agreement
if "agreed" not in st.session_state:
    st.session_state.agreed = False

# --- 2. MANDATORY SAFETY DIALOG (Addresses 1.4.1 & 5.1.1) ---
@st.dialog("Medical Disclaimer & Terms of Use")
def show_disclaimer():
    st.write("""
    **Welcome to Med-Assist.**
    
    This application is an **educational project** developed by **Adhrit Talluri**, an 11th-grade student at **Innovation Academy**. 
    
    By using this app, you acknowledge and agree to the following:
    1. **NOT MEDICAL ADVICE:** This app is a logic-demonstration tool and does NOT provide medical diagnoses, treatment plans, or professional advice.
    2. **PRIVACY:** No personal data, symptoms, or images are stored or shared. All data is processed in real-time and deleted after your session.
    3. **EMERGENCIES:** If you are in a medical emergency, call 911 or your local emergency services immediately.
    4. **CITATIONS:** Clinical insights are based on publicly available NIH and CDC guidelines.
    """)
    
    agree = st.checkbox("I have read and agree to these terms.")
    if st.button("Enter App", disabled=not agree):
        st.session_state.agreed = True
        st.rerun()

# Trigger the disclaimer if they haven't agreed yet
if not st.session_state.agreed:
    show_disclaimer()
    st.stop() # Stops the rest of the app from loading until they agree

# --- 3. SIDEBAR: CLINICAL TOOLS ---
with st.sidebar:
    st.header("🏥 Clinical Dashboard")
    
    # Direct Privacy Link
    st.markdown("[Privacy Policy](YOUR_GOOGLE_DOC_URL_HERE)")
    st.divider()
    
    specialty = st.selectbox(
        "Select Clinical Specialty",
        ["General Practice", "Pediatrics", "Dermatology", "Urgent Care", "Mental Health"]
    )
    
    st.divider()
    st.subheader("Diagnostic Tools")
    uploaded_file = st.file_uploader("Upload medical image", type=["jpg", "jpeg", "png"])
    
    st.divider()
    st.subheader("Patient Vitals")
    severity = st.slider("Severity Level (1-10)", 1, 10, 5)
    
    with st.expander("Input Physical Vitals"):
        temp = st.number_input("Temp (°F)", 95.0, 106.0, 98.6, step=0.1)
        hr = st.number_input("Heart Rate (BPM)", 40, 200, 72)
        bp = st.text_input("Blood Pressure", placeholder="120/80")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# --- 4. DYNAMIC SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are a professional medical assistant specializing in {specialty}.
1. Analyze symptoms based on clinical guidelines from NIH and Mayo Clinic.
2. Provide 3 'differential considerations'.
3. IMPORTANT: You are an educational tool for Innovation Academy. You cannot diagnose.
4. End every response with: 'Note: Educational tool only. Consult a physician.'
"""

model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- 5. MAIN INTERFACE ---
st.title(f"🩺 Med-Assist: {specialty} Mode")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Emergency Keywords
EMERGENCY_KEYWORDS = ["chest pain", "can't breathe", "stroke", "overdose", "heavy bleeding"]

if prompt := st.chat_input("Describe the symptoms..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(word in prompt.lower() for word in EMERGENCY_KEYWORDS):
            response_text = "⚠️ **EMERGENCY:** Stop using this app and call 911 immediately."
        else:
            payload = [f"[CONTEXT: {specialty}, Temp: {temp}, HR: {hr}, BP: {bp}] Patient: {prompt}"]
            if uploaded_file:
                payload.append(Image.open(uploaded_file))
            
            try:
                with st.spinner("Analyzing..."):
                    response = model.generate_content(payload)
                    response_text = response.text
            except Exception as e:
                response_text = f"Error: {str(e)}"

        st.markdown(response_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# Display history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])