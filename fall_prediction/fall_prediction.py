import streamlit as st
import pyttsx3
import pandas as pd
import os
from twilio.rest import Client
import google.generativeai as genai
import hashlib

# Set your Gemini API key
GEMINI_API_KEY = "AIzaSyAiWRuatBc3GlDdBkiRk7DwSZ6nPjbX8Js"
genai.configure(api_key=GEMINI_API_KEY)

# Function to generate chatbot responses
def chat_with_gemini(user_input):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_input)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI for the chatbot
def chatbot():
    st.subheader("💬 AI Chatbot")
    user_input = st.text_input("Ask me anything:")
    
    if st.button("Send"):
        if user_input:
            response = chat_with_gemini(user_input)
            st.write("🤖 AI Response:", response)
        else:
            st.warning("Please enter a message.")

# Twilio Credentials (Use environment variables for security)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACdc6f258e897aadb6c38e769124c2324c")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "37d7220577e73aaf75df345690af9cec")
TWILIO_PHONE_NUMBER = "+16282039907"
USER_PHONE_NUMBER = "+918074785887"

# Initialize Twilio Client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Text-to-Speech engine
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    st.write(text)

# Function to detect fall based on health parameters
def detect_fall(row):
    try:
        bp = float(row["BP"]) if pd.notna(row["BP"]) else 0
        hrv = float(row["HRV"]) if pd.notna(row["HRV"]) else 0
        spo2 = float(row["SpO2"]) if pd.notna(row["SpO2"]) else 0

        if bp < 90 or hrv < 30 or spo2 < 85:
            return "Fall Detected"
        return "No Fall"
    except ValueError:
        return "Invalid Data"

# Function to send SMS alert
def send_sms(message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER
        )
        st.write(f"[SMS Sent] {message}")
    except Exception as e:
        st.write(f"Error sending SMS: {e}")

# Function to make call alert
def make_call():
    try:
        client.calls.create(
            twiml="<Response><Say>Alert! A fall has been detected. Immediate attention is required.</Say></Response>",
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER
        )
        st.write("[Call Alert] Call initiated successfully.")
    except Exception as e:
        st.write(f"Error making call: {e}")

# --- Authentication Functions (Improved with Hashing) ---
def load_users():
    if os.path.exists("users.csv"):
        return pd.read_csv("users.csv", dtype=str)
    else:
        return pd.DataFrame(columns=["username", "password"])

def hash_password(password):  # Hash passwords for security
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(username, password):
    users = load_users()
    if username in users["username"].values:
        st.error("Username already exists!")
        return False
    hashed_password = hash_password(password)  # Hash before saving
    new_user = pd.DataFrame([[username, hashed_password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv("users.csv", index=False)
    st.success("Registration successful! Please login.")
    return True

def authenticate(username, password):
    users = load_users()
    if users.empty:  # Handle empty CSV
        return False
    user_row = users[users["username"] == username]
    if not user_row.empty:
        stored_password_hash = user_row["password"].iloc[0]
        return stored_password_hash == hash_password(password)  # Hash and compare
    return False

# Fall Detection Function
def fall_prediction():
    st.subheader("Fall Detection")
    days = [f"Day {i}" for i in range(1, 16)]
    default_values = {"BP": 120.0, "HRV": 70.0, "Sugar Levels": 100.0, "SpO2": 95.0}
    
    data = pd.DataFrame(index=days, columns=["BP", "HRV", "Sugar Levels", "SpO2"])
    
    for day in days:
        col1, col2, col3, col4 = st.columns(4)
        data.loc[day, "BP"] = col1.number_input(f"{day} BP", min_value=0.0, max_value=200.0, step=1.0, value=default_values["BP"])
        data.loc[day, "HRV"] = col2.number_input(f"{day} HRV", min_value=0.0, max_value=200.0, step=1.0, value=default_values["HRV"])
        data.loc[day, "Sugar Levels"] = col3.number_input(f"{day} Sugar", min_value=0.0, max_value=300.0, step=1.0, value=default_values["Sugar Levels"])
        data.loc[day, "SpO2"] = col4.number_input(f"{day} SpO2", min_value=50.0, max_value=100.0, step=1.0, value=default_values["SpO2"])
    
    if st.button("Check Fall Prediction"):
        data = data.astype(float)
        data["Fall Status"] = data.apply(detect_fall, axis=1)
        st.dataframe(data)
        
        if "Fall Detected" in data["Fall Status"].values:
            alert_message = "ALERT: Fall detected! Immediate attention required."
            send_sms(alert_message)
            make_call()
            speak("Fall Detected! Immediate attention required.")
            st.markdown("<p style='color:red; font-weight:bold;'>Fall Detected!</p>", unsafe_allow_html=True)
        else:
            speak("No fall detected. Stay safe!")
            st.success("No fall detected. Stay safe!")
        
        data.to_csv("fall_detection_data.csv", index=False)
        st.success("Data saved successfully!")

# Health Monitoring Function (Updated Parameters)
def health_conditions():
    st.subheader("Health Condition Monitoring")
    bp = st.number_input("Blood Pressure (BP)", min_value=50, max_value=200, value=120)
    hrv = st.number_input("Heart Rate Variability (HRV)", min_value=0, max_value=100, value=50)
    sugar_level = st.number_input("Sugar Levels", min_value=0, max_value=300, value=100)
    spo2 = st.number_input("SpO2 Level", min_value=50, max_value=100, value=95)

    if st.button("Check Health Condition"):
        message = ""
        speech_message = ""

        # BP Check
        if bp < 90:
            message += "⚠️ Warning! Low blood pressure detected.\n"
            speech_message += "Warning! Low blood pressure detected.\n  Drink water, eat something salty, and rest. If symptoms persist, consult a doctor. "
        elif bp > 140:
            message += "⚠️ Warning! High blood pressure detected.\n"
            speech_message += "Warning! High blood pressure detected. \n Take your prescribed medication, avoid salty foods, and relax. Consult a doctor if needed. "
        else:
            message += "✅ Blood pressure is in normal range.\n"
            speech_message += "Blood pressure is in normal range. "

        # HRV Check
        if hrv < 20:
            message += "⚠️ Warning! Low heart rate variability detected.\n"
            speech_message += "Warning! Low heart rate variability detected.\nTake a tablet if prescribed and eat something nutritious. "
        else:
            message += "✅ HRV levels are normal.\n"
            speech_message += "HRV levels are normal. "

        # Sugar Levels Check
        if sugar_level < 70:
            message += "⚠️ Warning! Low blood sugar detected.\n"
            speech_message += "Warning! Low blood sugar detected. \n Take glucose or eat something sugary immediately "
        elif sugar_level > 180:
            message += "⚠️ Warning! High blood sugar detected.\n"
            speech_message += "Warning! High blood sugar detected. \n Take your prescribed medication and follow a balanced diet "
        else:
            message += "✅ Blood sugar is in normal range.\n"
            speech_message += "Blood sugar is in normal range. "

        # SpO2 Level Check
        if spo2 < 90:
            message += "⚠️ Warning! Low oxygen levels detected.\n"
            speech_message += "Warning! Low oxygen levels detected.\n Take deep breaths, rest, and consider using oxygen support if needed. "
        else:
            message += "✅ SpO2 levels are normal.\n"
            speech_message += "SpO2 levels are normal. "

        # Display warnings in UI
        st.write(message)

        # Speak all health conditions (both normal & warnings)
        speak(speech_message)

# Health Guidelines Section
def health_guidelines():
    st.subheader("Health Guidelines")
    
    # Virtual Doctor Explanation
    st.markdown("### 🏥 Virtual Doctor Explanation")
    st.write("The virtual doctor will analyze your health parameters and provide recommendations based on the readings.")
    speak("Welcome to the health guidelines section. The virtual doctor will analyze your health parameters and provide recommendations.")

    # Website Workflow Guide
    st.markdown("### 🔄 Website Workflow Guide")
    st.write("1. Login or Register to access your health monitoring system.")
    st.write("2. Check for Fall Detection to monitor potential falls based on your health data.")
    st.write("3. Monitor your health conditions and receive real-time alerts.")
    st.write("4. Follow the Health Guidelines for better health management.")
    speak("This website allows you to monitor your health, check for falls, and receive alerts based on your data.")

    # Speech Output for Accessibility
    st.markdown("### 🗣️ Speech Output for Accessibility")
    st.write("For better accessibility, speech output is available for all major alerts and guidelines.")
    speak("Speech output is enabled to ensure accessibility for all users. Stay informed with real-time audio updates.")

# --- Streamlit App Layout ---
st.title("Health Monitoring System")

# Authentication State (Corrected)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.subheader("Login Section")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username # Store username
            st.success("Login successful!")
            st.experimental_rerun()  # Force re-run to update the menu
        else:
            st.error("Invalid credentials!")

def register():
    st.subheader("Register Section")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    if st.button("Register"):
        if save_user(username, password): # Check if registration is successful
            st.session_state.authenticated = True # Auto login after registration
            st.session_state.username = username # Store username
            st.experimental_rerun() # Force re-run to update the menu


# Conditional Menu and Content
menu_options = ["Login", "Register"]  # Default menu
if st.session_state.authenticated:
    menu_options = ["Fall Detection", "Health Conditions", "Health Guidelines", "Chatbot"]

menu = st.sidebar.selectbox("Menu", menu_options)

if menu == "Login":
    login()
elif menu == "Register":
    register()
elif menu == "Fall Detection":
    if st.session_state.authenticated:
        fall_prediction()
    else:
        st.error("Please login to access this feature.")
elif menu == "Health Conditions":
    health_conditions()
elif menu == "Health Guidelines":
    health_guidelines()
elif menu == "Chatbot":
    chatbot()
