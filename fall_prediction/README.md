# Health Monitoring System with Real-Time Alerts

## Overview
This project is a **Health Monitoring System** built using **Streamlit, Python, Machine Learning, and Twilio**. It provides real-time health condition monitoring, fall detection, chatbot support, and machine learning accuracy tracking. The system also includes voice-based alerts and SMS notifications for emergencies.

## Features
1. **User Registration & Login**
   - Secure authentication system with patient details storage.
   - Stores username, password, age, blood group, and food allergies.

2. **Health Condition Monitoring**
   - Monitors key health parameters:
     - Blood Pressure (BP)
     - Heart Rate Variability (HRV)
     - Blood Sugar Levels
     - SpO2 (Oxygen Levels)
   - Provides warnings and health recommendations based on readings.

3. **Fall Detection System**
   - Predicts falls based on health parameter thresholds.
   - Triggers **SMS alerts** and **emergency calls** via **Twilio API**.
   - Stores fall detection records for future reference.

4. **AI Chatbot**
   - Integrated with **Google Gemini AI** to answer health-related queries.
   - Provides recommendations and guidance through text-based AI responses.

5. **Machine Learning Accuracy Check**
   - Loads a pre-trained **SVM model** from a pickle file.
   - Displays real-time model accuracy using **scikit-learn**.

6. **Speech Output for Alerts**
   - Uses **pyttsx3** to provide voice alerts for health warnings and recommendations.

## Technologies Used
- **Frontend:** Streamlit
- **Backend:** Python (Flask not required as Streamlit handles UI and backend)
- **Machine Learning:** Scikit-Learn (SVM Model for fall prediction)
- **Voice Alerts:** pyttsx3
- **Database:** CSV-based storage for user data and fall detection logs
- **Twilio API:** For SMS and call alerts
- **Google Gemini AI:** For chatbot responses
