import streamlit as st
from PIL import Image
import json
import os
import pandas as pd
from transformers import pipeline

# --- PAGE CONFIG ---
st.set_page_config(page_title="Royal AI Pose Battle", page_icon="👑", layout="wide")

# --- LOAD EMBEDDED AI MODEL ---
@st.cache_resource(show_spinner="The Royal AI is awakening (this only happens once)...")
def load_ai():
    # Deploys a zero-shot vision model purely in Python. No API keys required.
    return pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

classifier = load_ai()

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

# --- AI VISION LOGIC ---
def analyze_pose(img_buffer):
    img = Image.open(img_buffer).convert("RGB")
    # The AI evaluates the image against these precise descriptions
    labels = [
        "a hand making a closed rock fist", 
        "a flat open paper hand", 
        "a hand showing two fingers peace sign scissors", 
        "a hand showing a thumbs up",
        "a person with no hands visible"
    ]
    
    results = classifier(img, candidate_labels=labels)
    best_match = results[0]["label"]
    
    if "fist" in best_match: return "Fist"
    elif "open" in best_match: return "Open Hand"
    elif "peace" in best_match or "two fingers" in best_match: return "Peace Sign"
    elif "thumbs up" in best_match: return "Thumbs Up"
    else: return "Unknown"

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
st.title("👑 Royal AI Pose Battle")
st.markdown("Your photos are processed directly on the server by an embedded Neural Network. **No API keys needed.** ✌️ 👍 🖐️ ✊")

col_names1, col_names2 = st.columns(2)
with col_names1:
    p1_name = st.text_input("Player 1 Name", "Player 1")
with col_names2:
    p2_name = st.text_input("Player 2 Name", "Player 2")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🛡️ {p1_name}'s Turn")
    p1_img = st.camera_input("Capture Pose", key="p1")

with col2:
    st.subheader(f"⚔️ {p2_name}'s Turn")
    p2_img = st.camera_input("Capture Pose", key="p2")

# THE FIX: The system no longer demands an API key to reveal the button
if p1_img and p2_img:
    st.markdown("---")
    if st.button("🏆 REVEAL WINNER!", use_container_width=True):
        with st.spinner("The Embedded AI is analyzing the gestures..."):
            p1_gesture = analyze_pose(p1_img)
            p2_gesture = analyze_pose(p2_img)
            
            st.success(f"**{p1_name}** deployed: {p1_gesture} | **{p2_name}** deployed: {p2_gesture}")
            
            winner = determine_winner(p1_gesture, p2_gesture, p1_name, p2_name)
            
            if winner == "Tie":
                st.warning("The battle ends in a draw! ⚔️")
            else:
                st.balloons()
                st.success(f"🎉 All hail {winner}, the Victor!")
                update_score(winner)

st.markdown("---")
st.header("🏆 The Grand Leaderboard")

if st.session_state.leaderboard:
    sorted_lb = sorted(st.session_state.leaderboard.items(), key=lambda x: x[1], reverse=True)
    best_player, top_score = sorted_lb[0]
    st.info(f"🌟 **Supreme Champion: {best_player} with {top_score} victories!** 🌟")
    
    # Chart Output
    df = pd.DataFrame(sorted_lb, columns=["Player", "Wins"]).set_index("Player")
    st.bar_chart(df)
else:
    st.write("The grand hall is empty. Claim your first victory.")
