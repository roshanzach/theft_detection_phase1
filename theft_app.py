import cv2
import streamlit as st
import threading
import time
from ultralytics import YOLO
from twilio.rest import Client

# Initialize YOLO model
model = YOLO("yolo11n.pt") 

st.set_page_config(page_title="AI Theft Prevention System", layout="wide")
st.title("🚨 Real-Time AI Theft Prevention Scanner")
st.caption("Adjust the sliders in the sidebar to dynamically position your Protected Safe Zone.")

# --- SIDEBAR CONFIGURATIONS ---
st.sidebar.header("🛡️ Security Configuration")

all_classes = sorted(list(model.names.values()))
default_targets = [item for item in ["laptop", "cell phone", "backpack", "wallet"] if item in all_classes]

selected_targets = st.sidebar.multiselect(
    "Select Items to Protect:",
    options=all_classes,
    default=default_targets if default_targets else [all_classes[0]]
)

BUFFER_THRESHOLD = st.sidebar.slider("Alert Delay Buffer (Frames)", min_value=10, max_value=100, value=30)

# --- FEATURE: VISUAL ROI SLIDERS (No Installation Required) ---
st.sidebar.markdown("---")
st.sidebar.header("🎨 Adjust Safe Zone Box")
roi_x = st.sidebar.slider("Box X Position (Left Edge)", min_value=0, max_value=640, value=150)
roi_y = st.sidebar.slider("Box Y Position (Top Edge)", min_value=0, max_value=480, value=100)
roi_w = st.sidebar.slider("Box Width", min_value=50, max_value=640, value=350)
roi_h = st.sidebar.slider("Box Height", min_value=50, max_value=480, value=320)

# Calculate final coordinates from sliders
ROI_ZONE = (roi_x, roi_y, roi_x + roi_w, roi_y + roi_h)

st.sidebar.markdown("---")
st.sidebar.header("📱 Twilio Settings")
channel = st.sidebar.selectbox("Notification Channel", ["SMS", "WhatsApp"])
TWILIO_ACCOUNT_SID = st.sidebar.text_input("Twilio Account SID", type="password")
TWILIO_AUTH_TOKEN = st.sidebar.text_input("Twilio Auth Token", type="password")
TWILIO_FROM_NUMBER = st.sidebar.text_input("Twilio Phone Number")
TO_NUMBER = st.sidebar.text_input("Your Personal Phone Number")

# --- BACKGROUND AUDIO ALARM FUNCTION ---
def play_siren_duration(sound_file, duration=10):
    """Plays audio using macOS native afplay and forcefully terminates it after X seconds."""
    import subprocess
    import time
    import os

    if not os.path.exists(sound_file):
        # Fallback system bell if file is missing
        start_time = time.time()
        while time.time() - start_time < duration:
            print('\a')
            time.sleep(10)
        return

    try:
        # Start afplay as a background system process
        process = subprocess.Popen(["afplay", sound_file])
        
        # Let it play for exactly the requested duration
        time.sleep(duration)
        
        # Forcefully terminate the audio process down to the millisecond
        process.terminate()
        process.wait() # Ensure resources are cleaned up
    except Exception as e:
        print(f"Audio Thread Error: {e}")

# --- TWILIO NOTIFICATION FUNCTION ---
def send_twilio_notification(message):
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_NUMBER]):
        return False
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        if channel == "WhatsApp":
            from_str = TWILIO_FROM_NUMBER if TWILIO_FROM_NUMBER.startswith("whatsapp:") else f"whatsapp:{TWILIO_FROM_NUMBER}"
            to_str = TO_NUMBER if TO_NUMBER.startswith("whatsapp:") else f"whatsapp:{TO_NUMBER}"
        else:
            from_str = TWILIO_FROM_NUMBER
            to_str = TO_NUMBER

        client.messages.create(body=message, from_=from_str, to=to_str)
        return True
    except Exception as e:
        print(f"Twilio Error: {e}")
        return False

# --- LAYOUT SETUP ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Security Camera Feed")
    frame_placeholder = st.empty()
with col2:
    st.subheader("Security Control Panel & Logs")
    alert_placeholder = st.empty()
    st.markdown("---")
    inventory_placeholder = st.empty()

start_monitoring = st.checkbox("▶️ Start Active Surveillance Core")

if start_monitoring:
    tracked_items = {}  
    security_alerts = []
    
    # Open live video feed tracking loop (Change to (0) on Windows/Linux)
    video = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION) 
    
    while video.isOpened():
        success, frame = video.read()
        if not success:
            st.error("Webcam stream disconnected.")
            break

        # Render the custom Safe Zone box dynamically updated by your sidebar sliders
        cv2.rectangle(frame, (ROI_ZONE[0], ROI_ZONE[1]), (ROI_ZONE[2], ROI_ZONE[3]), (255, 150, 0), 2)
        cv2.putText(frame, "PROTECTED SAFE ZONE", (ROI_ZONE[0], ROI_ZONE[1] - 8), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 150, 0), 2)

        # Run YOLO core tracking architecture
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)
        current_frame_ids = set()

        if results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            clss = results[0].boxes.cls.cpu().numpy().astype(int)
            names = model.names

            for box, track_id, cls in zip(boxes, track_ids, clss):
                obj_name = names[cls]
                if obj_name not in selected_targets:
                    continue

                x1, y1, x2, y2 = map(int, box)
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                current_frame_ids.add(track_id)

                if track_id not in tracked_items:
                    tracked_items[track_id] = {"name": obj_name, "missing_frames": 0, "last_position": (center_x, center_y)}
                else:
                    tracked_items[track_id]["missing_frames"] = 0
                    tracked_items[track_id]["last_position"] = (center_x, center_y)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 4, (0, 255, 0), -1)
                cv2.putText(frame, f"SECURED: {obj_name} [ID: {track_id}]", (x1, y1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Evaluate missing states and calculate boundary exceptions
        for tid, data in list(tracked_items.items()):
            if tid not in current_frame_ids:
                data["missing_frames"] += 1
                
                if data["missing_frames"] < BUFFER_THRESHOLD:
                    continue
                    
                last_x, last_y = data["last_position"]
                
                # Geofencing Validation Coordinates check
                if ROI_ZONE[0] <= last_x <= ROI_ZONE[2] and ROI_ZONE[1] <= last_y <= ROI_ZONE[3]:
                    alert_msg = f"❌ THEFT ALERT: Protected '{data['name']}' [ID: {tid}] vanished from Safe Zone!"
                    security_alerts.append(alert_msg)
                    
                    # A: SPIN UP AUDIO ALARM ON AN INDEPENDENT PYTHON THREAD (5 Secs)
                    audio_thread = threading.Thread(target=play_siren_duration, args=("alarm.mp3", 5))
                    audio_thread.daemon = True
                    audio_thread.start()
                    
                    # B: SEND CLOUD PHONE ALERTS ASYNCHRONOUSLY
                    notification_text = (
                        f"🚨 CRITICAL SECURITY BREACH 🚨\n\n"
                        f"An asset has been removed from the custom safe zone.\n"
                        f"• Item Type: {data['name'].upper()}\n"
                        f"• Tracker ID: {tid}"
                    )
                    send_twilio_notification(notification_text)
                    
                del tracked_items[tid]

        # Re-render frames on UI canvas
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, channels="RGB")
        
        active_items_list = [f"✅ Secure: {d['name']} (ID: {tid})" for tid, d in tracked_items.items() if d["missing_frames"] == 0]
        inventory_placeholder.write("**Items Tracked inside Room:**\n" + ("\n".join(active_items_list) if active_items_list else "_No targeted items in view._"))
        
        if security_alerts:
            alert_text = "\n".join([f"⚠️ {alert}" for alert in security_alerts[-8:]])
            alert_placeholder.error(f"**Security Violations Logged:**\n\n{alert_text}")
        else:
            alert_placeholder.success("✅ System Nominal: All assets secure inside slider-adjusted ROI.")
    
    video.release()