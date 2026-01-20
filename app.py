import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    st.error("API Configuration missing. Check Streamlit Secrets.")
    st.stop()

# --- CSS STYLE (Pitch & Positioning Fix) ---
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
        border: 3px solid white; height: 500px; width: 100%; position: relative; border-radius: 10px; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden;
    }
    .player-label {
        background: white; color: #1e2d24; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); border: 1px solid #2e7d32; white-space: nowrap; z-index: 100;
    }
    .match-card { background: white; padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .waiting-badge { background-color: #ffa500; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
def get_data():
    m = conn.table("matches").select("*").order("id", desc=True).limit(1).execute()
    match_data = m.data[0] if m.data else None
    joueurs_data = []
    if match_data:
        # We order by created_at to respect the "First come, first served" rule
        p = conn.table("participants").select("*").eq("match_id", match_data['id']).order("created_at").execute()
        joueurs_data = p.data if p.data else []
    return match_data, joueurs_data

match, joueurs = get_data()

# --- DURATION & LIMIT LOGIC ---
limite_joueurs = 10
duration_str = "N/A"
if match and match.get('heure_fin') and match.get('heure'):
    try:
        fmt = '%H:%M:%S' if len(match['heure']) > 5 else '%H:%M'
        start = datetime.strptime(match['heure'], fmt)
        end = datetime.strptime(match['heure_fin'], fmt)
        delta = (end - start).total_seconds() / 3600
        limite_joueurs = 12 if delta > 1 else 10
        duration_str = f"{delta:.1f}h"
    except: pass

# --- WAITING LIST LOGIC ---
main_squad = joueurs[:limite_joueurs]
waiting_list = joueurs[limite_joueurs:]

# --- ADMIN AUTH ---
with st.sidebar:
    st.header("🔐 Admin Panel")
    pw = st.text_input("Access Code", type="password")
    is_admin = (pw == "VOTRE_MOT_DE_PASSE")

# --- MAIN UI ---
st.title("⚽ Hali Saha Pro")

if match:
    st.markdown(f"""
    <div class="match-card">
        <h3>📅 Match: {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> ({duration_str})</p>
        <p>📍 {match['lieu']} | 👥 <b>{len(main_squad)} / {limite_joueurs} Players</b> (+{len(waiting_list)} waiting)</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📋 Registration", "🏟️ Tactical Pitch", "⚙️ Admin Tools"])

    with t1:
        st.link_button("🗺️ Get Directions", match['maps_url'], use_container_width=True)
        
        status_msg = f"Join the squad! ({len(main_squad)}/{limite_joueurs})" if len(main_squad) < limite_joueurs else "Squad is full. You will be added to the WAITING LIST."
        st.info(status_msg)
        
        with st.form("reg_form"):
            n = st.text_input("Your Name")
            p = st.selectbox("Preferred Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
            if st.form_submit_button("Confirm Registration"):
                if n:
                    conn.table("participants").insert({"match_id": match['id'], "nom_complet": n, "poste": p, "statut": "Confirmed ✅"}).execute()
                    st.rerun()

        if waiting_list:
            st.warning("⚠️ Waiting List Order:")
            for idx, w in enumerate(waiting_list):
                st.write(f"{idx+1}. {w['nom_complet']} ({w['poste']})")

    with t2:
        st.subheader("Starting Lineup")
        pitch_html = '<div class="pitch-container">'
        y_map = {"Forward": 18, "Midfielder": 42, "Defender": 68, "Goalkeeper": 88}
        
        for pos_name, y_top in y_map.items():
            at_pos = [j for j in main_squad if j['poste'] == pos_name]
            for i, p in enumerate(at_pos):
                x_left = (100 / (len(at_pos) + 1)) * (i + 1)
                pitch_html += f'<div class="player-label" style="top:{y_top}%; left:{x_left}%;">{p["nom_complet"]}</div>'
        
        pitch_html += '</div>'
        st.markdown(pitch_html, unsafe_allow_html=True)

    with t3:
        if is_admin:
            st.subheader("Edit Current Match")
            with st.form("edit_match"):
                new_l = st.text_input("Location", value=match['lieu'])
                new_h = st.text_input("Start Time", value=match['heure'])
                new_f = st.text_input("End Time", value=match['heure_fin'])
                new_m = st.text_input("Maps URL", value=match['maps_url'])
                if st.form_submit_button("Update Details"):
                    conn.table("matches").update({"lieu": new_l, "heure": new_h, "heure_fin": new_f, "maps_url": new_m}).eq("id", match['id']).execute()
                    st.rerun()
            
            st.divider()
            st.subheader("Manage Players")
            for j in joueurs:
                c1, c2 = st.columns([3, 1])
                is_waiting = " (Waiting List)" if j in waiting_list else ""
                c1.write(f"**{j['nom_complet']}**{is_waiting}")
                if c2.button("Kick", key=f"k_{j['id']}"):
                    conn.table("participants").delete().eq("id", j['id']).execute()
                    st.rerun()
        else:
            st.warning("Please enter the Admin Code in the sidebar.")

if is_admin:
    with st.sidebar.expander("🆕 Create New Match"):
        d = st.date_input("Date")
        h1 = st.time_input("Start")
        h2 = st.time_input("End")
        st_loc = st.text_input("Stadium")
        st_map = st.text_input("Maps Link")
        if st.button("Publish Match"):
            conn.table("matches").insert({"date": str(d), "heure": str(h1), "heure_fin": str(h2), "lieu": st_loc, "maps_url": st_map}).execute()
            st.rerun()
