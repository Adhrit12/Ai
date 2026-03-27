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

# --- 2. SIDEBAR: CLINICAL TOOLS ---
with st.sidebar:
    st.header("🏥 Clinical Dashboard")
    
    specialty = st.selectbox(
        "Select Clinical Specialty",
        ["General Practice", "Pediatrics", "Dermatology", "Urgent Care", "Mental Health"]
    )
    
    st.divider()
    
    st.subheader("Diagnostic Tools")
    uploaded_file = st.file_uploader(
        "Upload medical image", 
        type=["jpg", "jpeg", "png"],
        key="medical_image_upload"
    )
    
    st.divider()
    
    st.subheader("Patient Vitals")
    severity = st.slider("Severity Level (1-10)", 1, 10, 5)
    
    with st.expander("Input Physical Vitals"):
        temp = st.number_input("Temp (°F)", 95.0, 106.0, 98.6, step=0.1)
        hr = st.number_input("Heart Rate (BPM)", 40, 200, 72)
        bp = st.text_input("Blood Pressure", placeholder="120/80")
    
    st.divider()
    
    # Documentation Button
    generate_soap = st.button("📝 Generate SOAP Note")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# --- 3. DYNAMIC SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are a professional medical assistant specializing in {specialty}.
1. Analyze symptoms, images, and vitals through the lens of {specialty}.
2. Provide 3 'differential considerations'.
3. Highlight abnormal vitals.
4. End with: 'Disclaimer: I am an AI, not a doctor.'
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# --- 4. MAIN INTERFACE ---
st.title(f"🩺 Med-Assist: {specialty} Mode")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Logic for SOAP Note Generation
if generate_soap:
    if not st.session_state.chat_history:
        st.warning("No conversation history found to generate a note.")
    else:
        with st.spinner("Synthesizing clinical documentation..."):
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            soap_prompt = f"""
            Based on the following conversation and data, generate a professional SOAP note:
            Vitals: Temp {temp}, HR {hr}, BP {bp}. Severity {severity}/10.
            History: {history_text}
            
            Format as:
            - SUBJECTIVE: (Patient's reported symptoms)
            - OBJECTIVE: (Vitals and image findings)
            - ASSESSMENT: (Differential considerations)
            - PLAN: (Recommended next steps/clarifying questions)
            """
            soap_response = model.generate_content(soap_prompt)
            st.info("### Generated SOAP Note")
            st.text_area("Copy for Clinical Records", value=soap_response.text, height=300)
            st.download_button("Download Report", soap_response.text, file_name="clinical_note.txt")

# Display history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT LOGIC ---
EMERGENCY_KEYWORDS = ["chest pain", "can't breathe", "stroke", "overdose", "heavy bleeding"]

if prompt := st.chat_input("Describe the symptoms..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(word in prompt.lower() for word in EMERGENCY_KEYWORDS):
            response_text = "⚠️ **EMERGENCY:** Please call 911 immediately."
        else:
            clinical_context = f"[CONTEXT: {specialty}, Temp: {temp}, HR: {hr}, BP: {bp}] Patient: {prompt}"
            payload = [clinical_context]
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
