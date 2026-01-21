import streamlit as st
import pandas as pd
import random
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    url = st.secrets.get("SUPABASE_URL") or st.secrets["connections"]["supabase"]["url"]
    key = st.secrets.get("SUPABASE_KEY") or st.secrets["connections"]["supabase"]["key"]
    conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- CSS STYLE ---
st.markdown("""
    <style>
    :root { --card-bg: #ffffff; --card-text: #1e2d24; }
    @media (prefers-color-scheme: dark) {
        :root { --card-bg: #1e1e1e; --card-text: #ffffff; }
    }
    .match-card { 
        background-color: var(--card-bg); color: var(--card-text);
        padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 15px;
    }
    
    /* REALISTIC PITCH DESIGN */
    .pitch-container {
        background-color: #1a472a;
        background-image: 
            /* Grass Pattern */
            repeating-linear-gradient(90deg, transparent, transparent 10%, rgba(255,255,255,0.05) 10%, rgba(255,255,255,0.05) 20%),
            /* Center Line */
            linear-gradient(90deg, transparent 49.7%, rgba(255,255,255,0.8) 50%, transparent 50.3%),
            /* Center Circle */
            radial-gradient(circle at center, transparent 40px, rgba(255,255,255,0.8) 40px, rgba(255,255,255,0.8) 42px, transparent 42px);
        border: 4px solid rgba(255,255,255,0.9);
        height: 520px; width: 100%; position: relative; border-radius: 8px; margin-top: 20px; overflow: hidden;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
    }
    
    /* Goal Areas */
    .pitch-container::before, .pitch-container::after {
        content: ""; position: absolute; top: 25%; height: 50%; width: 50px; border: 2px solid rgba(255,255,255,0.8);
    }
    .pitch-container::before { left: -2px; border-radius: 0 10px 10px 0; }
    .pitch-container::after { right: -2px; border-radius: 10px 0 0 10px; }

    .player-label {
        padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 12px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 4px 6px rgba(0,0,0,0.4); 
        white-space: nowrap; z-index: 100; transition: all 0.3s;
    }
    .team-a { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; border: 1.5px solid white; }
    .team-b { background: linear-gradient(135deg, #991b1b, #ef4444); color: white; border: 1.5px solid white; }
    .no-team { background: #f8fafc; color: #1e293b; border: 1px solid #94a3b8; }
    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- DIALOGS ---
@st.dialog("Confirm Registration")
def confirm_registration(name, phone, level, match_id, is_waiting):
    st.write(f"**Name:** {name} | **Skill Level:** {'⭐' * level}")
    if is_waiting: st.warning("⚠️ Full. Joining Waiting List.")
    else: st.success("✅ Joining Main Squad.")
    if st.button("Confirm & Sign Up", use_container_width=True):
        conn.table("participants").insert({
            "match_id": match_id, "nom_complet": name, 
            "phone": phone, "level": level, "statut": "Confirmed ✅"
        }).execute()
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

# --- ADMIN PANEL ---
with st.sidebar:
    st.header("🔐 Admin Panel")
    pw = st.text_input("Access Code", type="password")
    is_admin = (pw == "foot!") # Replace with your password
    
    if is_admin:
        st.divider()
        with st.expander("🆕 Create New Match", expanded=not match):
            d = st.date_input("Match Date")
            col1, col2 = st.columns(2)
            h_start = col1.text_input("Start Time", "20:00")
            h_end = col2.text_input("End Time", "21:00")
            l = st.text_input("Stadium Name")
            m = st.text_input("Google Maps Link")
            if st.button("Publish Match", use_container_width=True):
                conn.table("matches").insert({"date": str(d), "heure": h_start, "heure_fin": h_end, "lieu": l, "maps_url": m, "is_finished": False}).execute()
                st.rerun()

# --- MAIN UI ---
st.title("⚽ Hali Saha Pro")

if match:
    limite_joueurs = 10
    main_squad = joueurs[:limite_joueurs]
    waiting_list = joueurs[limite_joueurs:]

    st.markdown(f"""
    <div class="match-card">
        <h3>📅 Match: {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> | 📍 {match['lieu']}</p>
        <p>👥 <b>{len(main_squad)} / {limite_joueurs} Players</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📋 Register", "🏟️ Balanced Pitch", "⚙️ Admin", "📜 History"])

    with t1:
        st.link_button("🗺️ Open Location", match['maps_url'], use_container_width=True)
        with st.form("reg_form"):
            n = st.text_input("Full Name")
            col_p1, col_p2 = st.columns([1, 4])
            col_p1.text_input("Country", "+32", disabled=True)
            ph_raw = col_p2.text_input("Phone Number", placeholder="470123456")
            lvl = st.select_slider("Select Skill Level", options=[1, 2, 3, 4, 5], value=3)
            if st.form_submit_button("Join Match", use_container_width=True):
                if n:
                    clean = "".join(filter(str.isdigit, ph_raw)).lstrip('0')
                    if clean.startswith("32"): clean = clean[2:]
                    confirm_registration(n, f"32{clean}", lvl, match['id'], len(main_squad) >= limite_joueurs)
                else: st.error("Please enter a name.")

    with t2:
        st.subheader("Balanced 1-2-2 Lineup")
        
        pitch_html = '<div class="pitch-container">'
        formation_coords = [{"y": 88, "x": 50}, {"y": 65, "x": 25}, {"y": 65, "x": 75}, {"y": 25, "x": 25}, {"y": 25, "x": 75}]
        
        team_a_p = [p for p in main_squad if p.get('team') == 'A']
        team_b_p = [p for p in main_squad if p.get('team') == 'B']
        others = [p for p in main_squad if p.get('team') not in ['A', 'B']]

        def draw_team(p_list, side):
            h = ""
            for i, p in enumerate(p_list[:5]):
                coords = formation_coords[i]
                x = (coords['x'] / 100) * 50 if side == "left" else 50 + (coords['x'] / 100) * 50
                t_cl = "team-a" if side == "left" else "team-b"
                h += f'<div class="player-label {t_cl}" style="top:{coords["y"]}%; left:{x}%;">{p["nom_complet"]}</div>'
            return h

        pitch_html += draw_team(team_a_p, "left")
        pitch_html += draw_team(team_b_p, "right")
        for i, p in enumerate(others):
            y_pos = 10 + (i * 8); pitch_html += f'<div class="player-label no-team" style="top:{y_pos}%; left:50%;">{p["nom_complet"]}</div>'
        st.markdown(pitch_html + '</div>', unsafe_allow_html=True)

    with t3:
        if is_admin:
            with st.expander("📥 Bulk Import & Skill Level"):
                bulk_input = st.text_area("Paste List (one name per line)", height=150)
                def_lvl = st.slider("Default skill for these players", 1, 5, 3)
                if st.button("Import Players", use_container_width=True):
                    for line in bulk_input.split('\n'):
                        name = "".join(filter(lambda x: not x.isdigit(), line)).replace(".", "").strip()
                        if name: conn.table("participants").insert({"match_id": match['id'], "nom_complet": name, "level": def_lvl, "statut": "Confirmed ✅"}).execute()
                    st.rerun()

            with st.expander("⚖️ Manage Player Levels & Teams"):
                st.write("Edit levels before balancing:")
                for j in joueurs:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.write(f"**{j['nom_complet']}**")
                    new_lvl = col2.select_slider("Level", options=[1,2,3,4,5], value=j.get('level', 3), key=f"lvl_{j['id']}")
                    if j.get('level') != new_lvl:
                        conn.table("participants").update({"level": new_lvl}).eq("id", j['id']).execute()
                        st.rerun()
                    if col3.button("❌", key=f"del_{j['id']}"):
                        conn.table("participants").delete().eq("id", j['id']).execute()
                        st.rerun()
                
                st.divider()
                if st.button("🔀 Generate Balanced Teams (Snake Draft)", use_container_width=True):
                    # Snake Draft: A, B, B, A, A, B, B, A, A, B
                    sorted_players = sorted(main_squad, key=lambda x: x.get('level', 3), reverse=True)
                    assignment = ['A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', 'B']
                    for i, p in enumerate(sorted_players):
                        if i < len(assignment):
                            conn.table("participants").update({"team": assignment[i]}).eq("id", p['id']).execute()
                    st.rerun()

                if st.button("🗑️ Reset Teams", type="secondary", use_container_width=True):
                    conn.table("participants").update({"team": None}).eq("match_id", match['id']).execute()
                    st.rerun()

            if any(p.get('team') for p in main_squad):
                    team_a = [p['nom_complet'] for p in main_squad if p.get('team') == 'A']
                    team_b = [p['nom_complet'] for p in main_squad if p.get('team') == 'B']
                    
                    # Formatting the message for WhatsApp
                    summary = f"⚽ *Teams:* \n\n*🔵 Team A:* {', '.join(team_a)}\n\n*🔴 Team B:* {', '.join(team_b)}"
                    encoded_msg = summary.replace(" ", "%20").replace("\n", "%0A")
                    share_url = f"https://wa.me/?text={encoded_msg}"
                    
                    # The button rendering
                    st.markdown(f'''
                        <a href="{share_url}" target="_blank" class="wa-btn" style="background-color:#075E54; width:100%; text-align:center; display:block; text-decoration:none;">
                            📲 Share Teams on WhatsApp Group
                        </a>
                    ''', unsafe_allow_html=True)

            with st.expander("📝 Edit Match & Archive"):
                with st.form("edit_details"):
                    u_lieu = st.text_input("Stadium", value=match['lieu'])
                    u_start = st.text_input("Start", value=match['heure'])
                    u_end = st.text_input("End", value=match.get('heure_fin', ''))
                    if st.form_submit_button("Update"):
                        conn.table("matches").update({"lieu": u_lieu, "heure": u_start, "heure_fin": u_end}).eq("id", match['id']).execute()
                        st.rerun()
                
                st.divider()
                sa, sb = st.number_input("Final Score: Team A", 0), st.number_input("Team B", 0)
                if st.button("Archive Match"):
                    conn.table("matches").update({"score_a": sa, "score_b": sb, "is_finished": True}).eq("id", match['id']).execute()
                    st.rerun()
        else: st.info("Enter admin code in sidebar.")

    with t4:
        for hm in history: st.write(f"📅 {hm['date']} | A {hm['score_a']} - {hm['score_b']} B")
else:
    st.info("No active match. Create one in the Sidebar.")
