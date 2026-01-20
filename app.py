import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    st.error("API Configuration missing.")
    st.stop()

# --- CSS STYLE (Interface & Pitch) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .pitch-container {
        background-color: #45a049;
        background-image: 
            linear-gradient(white 2px, transparent 2px),
            linear-gradient(90deg, white 2px, transparent 2px),
            radial-gradient(circle at center, transparent 0, transparent 40px, white 40px, white 42px, transparent 42px);
        background-size: 100% 50%, 50% 100%, 100% 100%;
        border: 3px solid white;
        height: 500px; width: 100%; position: relative; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .player-label {
        background: white; color: #1e2d24; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 11px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); border: 1px solid #2e7d32; white-space: nowrap; z-index: 10;
    }
    .match-card { background: white; padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .full-msg { background-color: #ff4b4b; color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOGIC ---
def get_data():
    m = conn.table("matches").select("*").order("id", desc=True).limit(1).execute()
    match_data = m.data[0] if m.data else None
    joueurs_data = []
    if match_data:
        p = conn.table("participants").select("*").eq("match_id", match_data['id']).execute()
        joueurs_data = p.data if p.data else []
    return match_data, joueurs_data

match, joueurs = get_data()

# --- LIMIT CALCULATION ---
limite_joueurs = 10 
duration_str = "Unknown duration"

if match and match.get('heure_fin') and match.get('heure'):
    try:
        fmt = '%H:%M:%S' if len(match['heure']) > 5 else '%H:%M'
        start_time = datetime.strptime(match['heure'], fmt)
        end_time = datetime.strptime(match['heure_fin'], fmt)
        delta = (end_time - start_time).total_seconds() / 3600
        if delta > 1:
            limite_joueurs = 12
        duration_str = f"{int(delta)}h" if delta.is_integer() else f"{delta}h"
    except:
        pass

presents = [j for j in joueurs if "✅" in j['statut']]
nb_presents = len(presents)
slots_left = limite_joueurs - nb_presents

# --- ADMIN SIDEBAR ---
with st.sidebar:
    st.header("🔐 Admin Space")
    pw = st.text_input("Admin Code", type="password")
    is_admin = (pw == "VOTRE_MOT_DE_PASSE")

# --- MAIN INTERFACE ---
st.title("⚽ Hali Saha Pro")

if match:
    st.markdown(f"""
    <div class="match-card">
        <h3>📅 Match on {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> ({duration_str})</p>
        <p>📍 {match['lieu']} | 👥 <b>{nb_presents} / {limite_joueurs} players</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📋 Registration", "🏟️ Pitch", "⚙️ Manage"])

    with t1:
        st.link_button("🗺️ Open in Google Maps", match['maps_url'], use_container_width=True)
        
        if slots_left <= 0:
            st.markdown('<div class="full-msg">🚫 FULL CAPACITY! Registration is closed.</div>', unsafe_allow_html=True)
        else:
            st.success(f"{slots_left} slots remaining!")
            with st.form("register_form"):
                n = st.text_input("First & Last Name")
                p = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
                if st.form_submit_button("Confirm Registration"):
                    if n:
                        # Logic maps French to English for DB consistency if needed, 
                        # but here we keep it simple with the selected label.
                        conn.table("participants").insert({
                            "match_id": match['id'], 
                            "nom_complet": n, 
                            "poste": p, 
                            "statut": "I'm coming ✅"
                        }).execute()
                        st.rerun()
                    else:
                        st.error("Name is required")

    with t2:
        st.subheader(f"Tactical Lineup ({nb_presents})")
        st.markdown('<div class="pitch-container">', unsafe_allow_html=True)
        
        y_coords = {"Forwards": 15, "Midfielders": 40, "Defenders": 65, "Goalkeeper": 88}
        mapping = {"Forward": "Forwards", "Midfielder": "Midfielders", "Defender": "Defenders", "Goalkeeper": "Goalkeeper"}

        for poste_db, poste_label in mapping.items():
            in_pos = [p for p in presents if p['poste'] == poste_db]
            for i, p in enumerate(in_pos):
                left = (100 / (len(in_pos) + 1)) * (i + 1)
                top = y_coords[poste_label]
                st.markdown(f'<div class="player-label" style="top:{top}%; left:{left}%;">{p["nom_complet"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        if is_admin:
            st.subheader("Remove Players")
            for j in joueurs:
                c1, c2 = st.columns([3, 1])
                c1.write(f"{j['nom_complet']}")
                if c2.button("Delete", key=f"d_{j['id']}"):
                    conn.table("participants").delete().eq("id", j['id']).execute()
                    st.rerun()
        else:
            st.info("Enter admin code in the sidebar to access management.")

if is_admin:
    with st.sidebar.expander("➕ Create New Match"):
        d = st.date_input("Date")
        h_d = st.time_input("Start Time")
        h_f = st.time_input("End Time")
        l = st.text_input("Stadium/Location")
        m = st.text_input("Maps Link")
        if st.button("Publish Match"):
            conn.table("matches").insert({
                "date": str(d), 
                "heure": str(h_d), 
                "heure_fin": str(h_f), 
                "lieu": l, 
                "maps_url": m
            }).execute()
            st.rerun()
