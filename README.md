# 🚨 AI Theft Prevention System

A real-time AI-powered theft detection application built using **Ultralytics YOLOv11**, **Streamlit**, and **Twilio**.

---

## 🌟 Features
- **Real-Time Object Detection**: Tracks items such as laptops, cell phones, backpacks, wallets, and people.
- **Custom Safe Zone (ROI)**: Dynamic sidebar sliders to configure and position a protected zone on screen.
- **Audible Siren Alert**: Automatically plays an alert sound when protected objects are removed from the safe zone.
- **Instant SMS / WhatsApp Alerts**: Sends notification messages with Twilio when a security breach is detected.
- **Interactive Web UI**: Powered by Streamlit with real-time frame rendering and status indicators.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY_NAME>.git
cd <YOUR_REPOSITORY_NAME>
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run theft_app.py
```

---

## ⚙️ Configuration
- **Safe Zone Adjustments**: Use the sidebar sliders to customize the bounding box around protected assets.
- **Twilio Setup**: Optional Twilio Account SID, Auth Token, and phone numbers in the sidebar for SMS/WhatsApp notifications.
