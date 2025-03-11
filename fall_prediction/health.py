import streamlit as st
import pickle
import pyttsx3
import pandas as pd
import os
from twilio.rest import Client
import google.generativeai as genai
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Load the dataset (same one used for training)
data_path = r"C:\Users\KEERTI\OneDrive\Documents\Desktop\fall prediction\fall_prediction\cStick_final.csv"
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip()  # Clean column names

# Define Features and Target
X = data.drop(columns=['Decision'], errors='ignore')
y = data['Decision']

# Scale Features (Same Preprocessing as Training)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Load the trained model from the Pickle file
model_path = r"C:\Users\KEERTI\OneDrive\Documents\Desktop\fall prediction\fall_prediction\svm_classifier.pkl"

def load_model():
    with open(model_path, "rb") as file:
        loaded_model = pickle.load(file)
    return loaded_model

def show_model_accuracy():
    model = load_model()
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    st.subheader("📊 Model Accuracy")
    st.write(f"✅ **SVM Model Accuracy: {accuracy:.2%}**")  # Display as percentage

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


# Define the CSV file for storing user data
USER_DATA_FILE = "patient_data.csv"

# Function to check if CSV file exists, if not create one
def initialize_user_data():
    if not os.path.exists(USER_DATA_FILE):
        df = pd.DataFrame(columns=["Username", "Password", "Age", "Blood Group", "Food Allergies"])
        df.to_csv(USER_DATA_FILE, index=False)

# Registration Function (Updated)
def register():
    st.subheader("Register New Patient")

    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    phone_number = st.text_input("Phone Number")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    food_allergies = st.text_area("Food Allergies (comma-separated)")

    if st.button("Register"):
        if new_username and new_password and phone_number:
            if os.path.exists(USER_DATA_FILE):
                user_data = pd.read_csv(USER_DATA_FILE)
                if new_username in user_data['Username'].values:
                    st.warning("Username already exists. Please choose a different username.")
                    return
            else:
                user_data = pd.DataFrame(columns=["Username", "Password", "Phone Number", "Age", "Blood Group", "Food Allergies"])

            new_data = pd.DataFrame([[new_username, new_password, phone_number, age, blood_group, food_allergies]],
                                    columns=["Username", "Password", "Phone Number", "Age", "Blood Group", "Food Allergies"])

            user_data = pd.concat([user_data, new_data], ignore_index=True)
            user_data.to_csv(USER_DATA_FILE, index=False)

            st.success(f"User {new_username} registered successfully!")
            speak(f"User {new_username} registered successfully!")
        else:
            st.warning("Please enter all details!")

# Login Function
def login():
    st.markdown(
        """
        <style>
        .top-right {
            position: absolute;
            top: -60px;   /* Adjust the vertical position */
            right: -30px; /* Adjust the horizontal position */
            width: 285px; /* Adjust width */
            height: auto; /* Maintain aspect ratio */
            transform: scaleX(-1); /* Flip horizontally */
        }
        </style>
        <img class="top-right" src="https://media.istockphoto.com/id/874103026/photo/heart-stethoscope.jpg?s=612x612&w=0&k=20&c=tjQ8Y2R-x4LToTYHbGBUZ41AlZQLbHO2ixqXQOzwrUw=">
        """,
        unsafe_allow_html=True
    )
    # 📌 Image beside login (right-center)
    st.markdown(
        """
        <style>
        .right-center {
            position: absolute;
            top: 30%;   /* Move to center vertically */
            right: -300px; /* Adjust horizontal position */
            transform: translateY(-30%); /* Perfectly center the image */
            width: 280px; /* Adjust width */
            height: 400px; /* Maintain aspect ratio */
        }
        </style>
        <img class="right-center" src="https://t3.ftcdn.net/jpg/02/25/70/62/360_F_225706206_woz4jU74GHRLbpbsftuhAYXH8ua7ZUZL.jpg">
        """,
        unsafe_allow_html=True
    )

    st.subheader("Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password").strip()
    if st.button("Login"):
        if os.path.exists(USER_DATA_FILE):
            user_data = pd.read_csv(USER_DATA_FILE, dtype={'Password': str}) # force password to be string
            user_row = user_data[user_data["Username"].str.strip() == username]

            if not user_row.empty and user_row.iloc[0]["Password"].strip() == password:
                st.success(f"Logged in as {username}")
                speak(f"Logged in as {username}")
                st.session_state.logged_in = True
                st.session_state.username = username
            else:
                st.error("Invalid username or password.")
        else:
            st.error("No users registered. Please register first.")




# Default values for inputs
default_values = {"BP": 120.0, "HRV": 70.0, "Sugar Levels": 100.0, "SpO2": 95.0}
FALL_DETECTION_FILE = "fall_detection_data.csv"

# Initialize CSV file if not exists
def initialize_fall_data():
    if not os.path.exists(FALL_DETECTION_FILE):
        df = pd.DataFrame(columns=["Day", "BP", "HRV", "Sugar Levels", "SpO2", "Fall Status"])
        df.to_csv(FALL_DETECTION_FILE, index=False)

# Function to detect fall based on predefined conditions
def detect_fall(row):
    if row["BP"] < 90 or row["SpO2"] < 90:
        return "Fall Detected"
    return "No Fall"

# Fall prediction function
def fall_prediction():
    st.subheader("Fall Detection")

    days = [f"Day {i}" for i in range(1, 16)]
    
    data = pd.DataFrame(index=days, columns=["BP", "HRV", "Sugar Levels", "SpO2"])

    for day in days:
        col1, col2, col3, col4 = st.columns(4)

        # Use default values if no input is provided
        data.loc[day, "BP"] = col1.number_input(f"{day} BP", min_value=0.0, max_value=200.0, step=1.0, value=default_values["BP"])
        data.loc[day, "HRV"] = col2.number_input(f"{day} HRV", min_value=0.0, max_value=200.0, step=1.0, value=default_values["HRV"])
        data.loc[day, "Sugar Levels"] = col3.number_input(f"{day} Sugar", min_value=0.0, max_value=300.0, step=1.0, value=default_values["Sugar Levels"])
        data.loc[day, "SpO2"] = col4.number_input(f"{day} SpO2", min_value=50.0, max_value=100.0, step=1.0, value=default_values["SpO2"])

    if st.button("Check Fall Prediction"):
        data["Fall Status"] = data.apply(detect_fall, axis=1)

        if "Fall Detected" in data["Fall Status"].values:
            # Send alerts
            send_sms("ALERT: Fall detected! Immediate attention required.")
            make_call()
            speak("Fall Detected! Immediate attention required.")
            st.markdown("<p style='color:red; font-weight:bold;'>Fall Detected!</p>", unsafe_allow_html=True)
        else:
            speak("No fall detected. Stay safe!")
            st.success("No fall detected. Stay safe!")

        # Load existing fall detection data
        if os.path.exists(FALL_DETECTION_FILE):
            fall_data = pd.read_csv(FALL_DETECTION_FILE)
        else:
            fall_data = pd.DataFrame(columns=["Day", "BP", "HRV", "Sugar Levels", "SpO2", "Fall Status"])

        # Append new data
        data["Day"] = days  # Add day column
        fall_data = pd.concat([fall_data, data], ignore_index=True)
        fall_data.to_csv(FALL_DETECTION_FILE, index=False)

        st.success("Fall detection data saved successfully!")

# Initialize CSV before running Streamlit app
initialize_fall_data()

# Health Monitoring Function (Updated Parameters)
def health_conditions():
    st.subheader("🩺 Health Condition Monitoring")
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

# Streamlit App Layout
st.markdown("<h1 style='text-align: center; color: black;'>Health Monitoring System with Real Time Alerts</h1>", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

initialize_user_data()  # Initialize user data 

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])
    if menu == "Login":
        login()
    elif menu == "Register":
        register()
else:
    menu = st.sidebar.selectbox("Menu", ["Fall Detection", "Health Conditions", "Health Guidelines", "Chatbot", "ML Accuracy"])
    if menu == "Fall Detection":
        fall_prediction()
    elif menu == "Health Conditions":
        health_conditions()
    elif menu == "Health Guidelines":
        health_guidelines() 
    elif menu == "Chatbot":
        chatbot()
    elif menu == "ML Accuracy":
        show_model_accuracy()
