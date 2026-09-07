import sys
import subprocess

# --- SURGICAL CLOUD PATCH ---
try:
    import cv2
except ImportError:
    # Catch libGL/GUI errors caused by mediapipe's forced dependencies
    # and forcefully overwrite them with the headless binaries at runtime.
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "opencv-python-headless==4.9.0.80", "--force-reinstall", "--no-deps"
    ])
    if "cv2" in sys.modules:
        del sys.modules["cv2"]
    import cv2

import streamlit as st
import mediapipe as mp
import numpy as np
from PIL import Image
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Pose Battle", page_icon="✌️", layout="wide")

# --- INITIALIZE MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)

# --- STATE & LEADERBOARD ---
LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_leaderboard(lb):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(lb, f)

if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = load_leaderboard()

def update_score(player_name):
    if player_name not in st.session_state.leaderboard:
        st.session_state.leaderboard[player_name] = 0
    st.session_state.leaderboard[player_name] += 1
    save_leaderboard(st.session_state.leaderboard)

# --- GESTURE LOGIC ---
def get_gesture(hand_landmarks):
    fingers = []
    # Check Index, Middle, Ring, Pinky 
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y else 0)
    
    thumb_up = 1 if hand_landmarks.landmark[4].y < hand_landmarks.landmark[2].y else 0
    up_count = sum(fingers)
    
    if up_count == 0 and thumb_up == 1:
        return "Thumbs Up"
    elif up_count == 2 and fingers[0] == 1 and fingers[1] == 1:
        return "Peace Sign"
    elif up_count >= 3:
        return "Open Hand"
    elif up_count == 0 and thumb_up == 0:
        return "Fist"
    else:
        return "Unknown"

def process_image(img_buffer):
    img = Image.open(img_buffer).convert('RGB')
    img_array = np.array(img)
    results = hands.process(img_array)
    
    gesture = "No Hand Detected"
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            gesture = get_gesture(hand_landmarks)
            mp_drawing.draw_landmarks(img_array, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
    return img_array, gesture

def determine_winner(m1, m2, p1, p2):
    valid_moves = ["Fist", "Open Hand", "Peace Sign", "Thumbs Up"]
    if m1 not in valid_moves and m2 not in valid_moves: return "Tie"
    if m1 not in valid_moves: return p2
    if m2 not in valid_moves: return p1
    if m1 == m2: return "Tie"
    
    if m1 == "Thumbs Up": return p1
    if m2 == "Thumbs Up": return p2
    
    if m1 == "Fist" and m2 == "Peace Sign": return p1
    if m1 == "Open Hand" and m2 == "Fist": return p1
    if m1 == "Peace Sign" and m2 == "Open Hand": return p1
    
    return p2

# --- UI ---
st.title("🤖 AI Pose Battle")
st.markdown("Take turns snapping your best pose. **Thumbs Up** is the ultimate power move! ✌️ 👍 🖐️ ✊")

col_names1, col_names2 = st.columns(2)
with col_names1:
    p1_name = st.text_input("Player 1 Name", "Player 1")
with col_names2:
    p2_name = st.text_input("Player 2 Name", "Player 2")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🛡️ {p1_name}'s Turn")
    p1_img = st.camera_input("Take your pose", key="p1")
    p1_gesture = None
    if p1_img:
        processed, p1_gesture = process_image(p1_img)
        st.image(processed, caption=f"AI Detected: {p1_gesture}")

with col2:
    st.subheader(f"⚔️ {p2_name}'s Turn")
    p2_img = st.camera_input("Take your pose", key="p2")
    p2_gesture = None
    if p2_img:
        processed, p2_gesture = process_image(p2_img)
        st.image(processed, caption=f"AI Detected: {p2_gesture}")

if p1_img and p2_img and p1_gesture and p2_gesture:
    st.markdown("---")
    if st.button("🏆 REVEAL WINNER!", use_container_width=True):
        winner = determine_winner(p1_gesture, p2_gesture, p1_name, p2_name)
        
        if winner == "Tie":
            st.warning("It's a Tie! ⚔️")
        elif winner == p1_name:
            st.success(f"🎉 {p1_name} Wins with {p1_gesture}!")
            update_score(p1_name)
            st.balloons()
        elif winner == p2_name:
            st.success(f"🎉 {p2_name} Wins with {p2_gesture}!")
            update_score(p2_name)
            st.balloons()

st.markdown("---")
st.header("🏆 Global Leaderboard")

sorted_lb = sorted(st.session_state.leaderboard.items(), key=lambda x: x[1], reverse=True)

if sorted_lb:
    best_player, top_score = sorted_lb[0]
    st.info(f"🌟 **Top Gamer Banner: {best_player} with {top_score} wins!** 🌟")
    cols = st.columns(4)
    for idx, (player, score) in enumerate(sorted_lb):
        cols[idx % 4].metric(label=f"#{idx+1} {player}", value=f"{score} wins")
else:
    st.write("No matches played yet. Be the first to get on the board!")
