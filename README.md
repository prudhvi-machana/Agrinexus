# Agrinexus-DBMS--Project
  
Agriculture plays a vital role in many economies, but farmers often face challenges accessing the information they need to improve their livelihoods. Simultaneously, governments and agricultural researchers require accurate, centralized data to make informed decisions.

However, the absence of a unified system to manage crop details, government subsidies, and loans creates a significant gap—hindering effective planning and support.

To bridge this gap, we developed Agrinexus: a comprehensive Database Management System with a user-friendly interface that consolidates all essential agricultural information into a single platform.

📌 This project was developed as part of our Database Management Systems (DBMS) Minor Project coursework.
## Table of Contents
- [Installation](#installation)
- [Twilio Integration](#twilio-integration)
- [Run the Project](#run-the-project)
- [Usage](#usage)
- [Contributors](#contributors)
  
## Installation
#### 1.Clone the Repository
```bash
git@github.com:PavithraNelluri/Agrinexus-DBMS-Minor-Project-.git
```
#### 2.Create a Virtual Environment
```bash
python -m venv venv
```
#### 3.Activate the virtual environment
- On Windows
```bash
venv/Scripts/activate
```
- On macOS/Linux:
```bash
  source venv/bin/activate
```
#### 4.Install Dependencies
```bash
pip install -r requirements.txt
```
##  Twilio Integration
We use Twilio API to send a welcome message to farmers upon their first login.
### 🔑 Setup Instructions:
#### 1.Sign up for a free or paid Twilio account.
#### 2.Get your:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER
#### 3.Create a .env file in the root directory and add your credentials:
```ini
ACCOUNT_SID=your_account_sid
AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
```
#### 4.Important: With a free Twilio account, you can only send messages to verified phone numbers.
## Run the Project
Once setup is complete, start the application with: 
```bash
python app.py
```

