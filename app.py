import streamlit as st
import base64
import requests
from PIL import Image
import json
import os
import io
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Pose Battle", page_icon="🤖", layout="wide")

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

# --- AI VISION LOGIC (DIRECT REST API) ---
def analyze_pose(img_buffer):
    api_key = "AQ.Ab8RN6LvHE-Ux4l_KdfpBCLzpCooB5OISDbXH3cq5AT8unaS3A"
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # Bypassing SDKs to force the new AQ. key format through standard headers
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # Standardize image to JPEG for the payload
    img = Image.open(img_buffer).convert("RGB")
    b = io.BytesIO()
    img.save(b, format="JPEG")
    b64_img = base64.b64encode(b.getvalue()).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this image. Is the person showing a 'Fist', 'Open Hand', 'Peace Sign', or 'Thumbs Up'? Reply with strictly one of these four options."},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
            ]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip().title()
        else:
            return f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Request Error: {str(e)}"

def determine_winner(m1, m2, p1, p2):
    valid_moves = ["Fist", "Open Hand", "Peace Sign", "Thumbs Up"]
    if "Error" in m1 or "Error" in m2: return "Error"
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
st.markdown("The Arena is open. **Thumbs Up** is the ultimate power move. ✌️ 👍 🖐️ ✊")

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

if p1_img and p2_img:
    st.markdown("---")
    if st.button("🏆 REVEAL WINNER!", use_container_width=True):
        with st.spinner("The AI is analyzing the battlefield..."):
            p1_gesture = analyze_pose(p1_img)
            p2_gesture = analyze_pose(p2_img)
            
            st.success(f"**{p1_name}** deployed: {p1_gesture} | **{p2_name}** deployed: {p2_gesture}")
            
            winner = determine_winner(p1_gesture, p2_gesture, p1_name, p2_name)
            
            if winner == "Error":
                st.error("The API connection failed. Please check the exact error message displayed above.")
            elif winner == "Tie":
                st.warning("The battle ends in a draw! ⚔️")
            else:
                st.balloons()
                st.success(f"🎉 Winner: {winner}!")
                update_score(winner)

st.markdown("---")
st.header("🏆 Global Leaderboard")

if st.session_state.leaderboard:
    sorted_lb = sorted(st.session_state.leaderboard.items(), key=lambda x: x[1], reverse=True)
    best_player, top_score = sorted_lb[0]
    st.info(f"🌟 **Top Gamer: {best_player} with {top_score} wins!** 🌟")
    
    # Chart Output
    df = pd.DataFrame(sorted_lb, columns=["Player", "Wins"]).set_index("Player")
    st.bar_chart(df)
else:
    st.write("No matches played yet. Claim your first victory.")
