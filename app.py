import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

# Tentative de récupération des clés dans les secrets
try:
    # On essaie d'abord la méthode automatique
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    # Si ça échoue, on force avec les paramètres manuels
    url = st.secrets.get("SUPABASE_URL") or st.secrets["connections"]["supabase"]["url"]
    key = st.secrets.get("SUPABASE_KEY") or st.secrets["connections"]["supabase"]["key"]
    conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- CSS STYLE ---
st.markdown("""
    <style>
    :root { --card-bg: #ffffff; --card-text: #1e2d24; --pitch-line: white; }
    @media (prefers-color-scheme: dark) {
        :root { --card-bg: #1e1e1e; --card-text: #ffffff; --pitch-line: rgba(255,255,255,0.6); }
        .stApp { background-color: #0e1117; }
    }
    .match-card { 
        background-color: var(--card-bg); color: var(--card-text);
        padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 15px;
    }
    .pitch-container {
        background-color: #2d5a27;
        background-image: 
            linear-gradient(var(--pitch-line) 2px, transparent 2px),
            linear-gradient(90deg, var(--pitch-line) 2px, transparent 2px),
            radial-gradient(circle at center, transparent 0, transparent 40px, var(--pitch-line) 40px, var(--pitch-line) 42px, transparent 42px);
        background-size: 100% 50%, 50% 100%, 100% 100%;
        border: 3px solid var(--pitch-line); height: 500px; width: 100%; position: relative; border-radius: 10px; margin-top: 20px; overflow: hidden;
    }
    .player-label {
        padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); white-space: nowrap; z-index: 100;
    }
    .team-a { background: #3b82f6; color: white; border: 1px solid white; }
    .team-b { background: #ef4444; color: white; border: 1px solid white; }
    .no-team { background: white; color: black; border: 1px solid #2e7d32; }
    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- DIALOGS ---
@st.dialog("Confirm Registration")
def confirm_registration(name, phone, position, match_id, is_waiting):
    st.write(f"**Name:** {name} | **Position:** {position}")
    if is_waiting: st.warning("⚠️ You will join the Waiting List.")
    else: st.success("✅ Joining Main Squad.")
    if st.button("Confirm", use_container_width=True):
        conn.table("participants").insert({"match_id": match_id, "nom_complet": name, "phone": phone, "poste": position, "statut": "Confirmed ✅"}).execute()
        st.rerun()

# --- DATA FETCHING ---
def get_data():
    m = conn.table("matches").select("*").eq("is_finished", False).order("id", desc=True).limit(1).execute()
    match_data = m.data[0] if m.data else None
    h = conn.table("matches").select("*").eq("is_finished", True).order("date", desc=True).limit(5).execute()
    joueurs_data = []
    if match_data:
        p = conn.table("participants").select("*").eq("match_id", match_data['id']).order("created_at").execute()
        joueurs_data = p.data if p.data else []
    return match_data, joueurs_data, h.data

match, joueurs, history = get_data()

# --- ADMIN AUTH ---
with st.sidebar:
    st.header("🔐 Admin Panel")
    pw = st.text_input("Access Code", type="password")
    is_admin = (pw == "VOTRE_MOT_DE_PASSE")

# --- UI ---
if match:
    limite_joueurs = 10 # Adjust logic for 12 if needed
    main_squad = joueurs[:limite_joueurs]
    waiting_list = joueurs[limite_joueurs:]

    st.markdown(f'<div class="match-card"><h3>📅 Match: {match["date"]}</h3><p>⏱️ {match["heure"]} | 📍 {match["lieu"]}</p></div>', unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📋 Register", "🏟️ Pitch & Teams", "⚙️ Admin", "📜 History"])

    with t1:
        with st.form("reg"):
            n = st.text_input("Name")
            ph_raw = st.text_input("Phone (e.g. 0470...)", placeholder="Belgian number")
            p = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
            if st.form_submit_button("Join Match"):
                clean = "".join(filter(str.isdigit, ph_raw)).lstrip('0').replace('32', '')
                confirm_registration(n, f"32{clean}", p, match['id'], len(main_squad) >= limite_joueurs)

    with t2:
        st.subheader("Team Distribution")
        # Pitch mapping
        pitch_html = '<div class="pitch-container">'
        y_map = {"Forward": 18, "Midfielder": 42, "Defender": 68, "Goalkeeper": 88}
        
        for pos_name, y_top in y_map.items():
            at_pos = [j for j in main_squad if j['poste'] == pos_name]
            for i, p in enumerate(at_pos):
                x_left = (100 / (len(at_pos) + 1)) * (i + 1)
                team_class = "team-a" if p.get('team') == 'A' else "team-b" if p.get('team') == 'B' else "no-team"
                pitch_html += f'<div class="player-label {team_class}" style="top:{y_top}%; left:{x_left}%;">{p["nom_complet"]}</div>'
        
        st.markdown(pitch_html + '</div>', unsafe_allow_html=True)
        
        if any(j.get('team') for j in main_squad):
            c1, c2 = st.columns(2)
            c1.markdown("### 🔵 Team A")
            for j in [p for p in main_squad if p.get('team') == 'A']: c1.write(f"- {j['nom_complet']} ({j['poste']})")
            c2.markdown("### 🔴 Team B")
            for j in [p for p in main_squad if p.get('team') == 'B']: c2.write(f"- {j['nom_complet']} ({j['poste']})")

    with t3:
        if is_admin:
            if len(main_squad) >= 10:
                if st.button("🔀 Generate Random Teams"):
                    players = main_squad.copy()
                    random.shuffle(players)
                    for i, p in enumerate(players):
                        team = 'A' if i % 2 == 0 else 'B'
                        conn.table("participants").update({"team": team}).eq("id", p['id']).execute()
                    st.success("Teams Generated! Check the Pitch tab.")
                    st.rerun()
            else:
                st.info("Wait for 10 players to generate teams.")
            
            # (Rest of Admin tools: End Match, Kick, Reminders... as per previous version)
            st.divider()
            if st.button("📢 Send WhatsApp Team List"):
                team_a = [p['nom_complet'] for p in main_squad if p.get('team') == 'A']
                team_b = [p['nom_complet'] for p in main_squad if p.get('team') == 'B']
                msg = f"⚽ Teams for {match['date']}: \n\nTeam A: {', '.join(team_a)}\n\nTeam B: {', '.join(team_b)}"
                st.write(f"[Send to Group](https://wa.me/?text={msg.replace(' ', '%20').replace('\\n', '%0A')})")

    with t4:
        for hm in history: st.write(f"📅 {hm['date']} | Team A {hm['score_a']} - {hm['score_b']} Team B")
else:
    st.info("No active match.")
    if is_admin:
        if st.sidebar.button("Create New Match"):
            # Simplified insert for demo
            conn.table("matches").insert({"date": str(datetime.now().date()), "heure": "20:00", "is_finished": False}).execute()
            st.rerun()
