import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    url = st.secrets.get("SUPABASE_URL") or st.secrets["connections"]["supabase"]["url"]
    key = st.secrets.get("SUPABASE_KEY") or st.secrets["connections"]["supabase"]["key"]
    conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- SMART UI & DARK MODE CSS ---
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
    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
    .team-a { background: #3b82f6 !important; color: white !important; border: 2px solid white !important; }
    .team-b { background: #ef4444 !important; color: white !important; border: 2px solid white !important; }
    .no-team { background: white !important; color: black !important; border: 1px solid #2e7d32 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DIALOGS ---
@st.dialog("Confirm Registration")
def confirm_registration(name, phone, position, match_id, is_waiting):
    st.write(f"**Name:** {name} | **Phone:** +{phone}")
    if is_waiting: st.warning("⚠️ You will join the **Waiting List**.")
    else: st.success("✅ Joining the **Main Squad**.")
    if st.button("Confirm & Sign Up", use_container_width=True):
        conn.table("participants").insert({
            "match_id": match_id, "nom_complet": name, 
            "phone": phone, "poste": position, "statut": "Confirmed ✅"
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

# --- ADMIN AUTH ---
with st.sidebar:
    st.header("🔐 Admin Panel")
    pw = st.text_input("Access Code", type="password")
    is_admin = (pw == "VOTRE_MOT_DE_PASSE")

# --- MAIN UI ---
st.title("⚽ Hali Saha Pro")

if match:
    limite_joueurs = 10
    try:
        fmt = '%H:%M:%S' if len(match['heure']) > 5 else '%H:%M'
        delta = (datetime.strptime(match['heure_fin'], fmt) - datetime.strptime(match['heure'], fmt)).total_seconds() / 3600
        limite_joueurs = 12 if delta > 1 else 10
    except: pass
    
    main_squad = joueurs[:limite_joueurs]
    waiting_list = joueurs[limite_joueurs:]

    st.markdown(f"""
    <div class="match-card">
        <h3>📅 Next Match: {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> | 📍 {match['lieu']}</p>
        <p>👥 <b>{len(main_squad)} / {limite_joueurs} Players</b> (+{len(waiting_list)} waiting)</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📋 Register", "🏟️ Pitch", "⚙️ Admin", "📜 History"])

    with t1:
        st.link_button("🗺️ Open Location", match['maps_url'], use_container_width=True)
        with st.form("reg_form"):
            n = st.text_input("Full Name")
            col1, col2 = st.columns([1, 4])
            col1.text_input("Country", "+32", disabled=True)
            ph_raw = col2.text_input("Phone Number", placeholder="470123456")
            p = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
            if st.form_submit_button("Join Match", use_container_width=True):
                if n and ph_raw:
                    clean_digits = "".join(filter(str.isdigit, ph_raw))
                    if clean_digits.startswith("32"): clean_digits = clean_digits[2:]
                    elif clean_digits.startswith("0"): clean_digits = clean_digits[1:]
                    final_phone = f"32{clean_digits}"
                    confirm_registration(n, final_phone, p, match['id'], len(main_squad) >= limite_joueurs)
                else: st.error("Name and Phone are required.")

    with t2:
        st.subheader("Tactical Lineup")
        pitch_html = '<div class="pitch-container">'
        y_map = {"Forward": 18, "Midfielder": 42, "Defender": 68, "Goalkeeper": 88}
        for pos_name, y_top in y_map.items():
            at_pos = [j for j in main_squad if j['poste'] == pos_name]
            for i, p in enumerate(at_pos):
                x_left = (100 / (len(at_pos) + 1)) * (i + 1)
                t_val = p.get('team')
                team_class = "team-a" if t_val == 'A' else "team-b" if t_val == 'B' else "no-team"
                pitch_html += f'<div class="player-label {team_class}" style="top:{y_top}%; left:{x_left}%;">{p["nom_complet"]}</div>'
        pitch_html += '</div>'
        st.markdown(pitch_html, unsafe_allow_html=True)

    with t3:
        if is_admin:
            st.subheader("🛠️ Edit Match")
            with st.form("edit_match"):
                u_l = st.text_input("Location", value=match['lieu'])
                u_h = st.text_input("Start", value=match['heure'])
                u_f = st.text_input("End", value=match['heure_fin'])
                if st.form_submit_button("Save Changes"):
                    conn.table("matches").update({"lieu": u_l, "heure": u_h, "heure_fin": u_f}).eq("id", match['id']).execute()
                    st.rerun()

            st.divider()
            st.subheader("🔀 Team Management")
            if len(main_squad) >= 10:
                if st.button("Generate Random Teams"):
                    players_to_shuffle = main_squad.copy()
                    random.shuffle(players_to_shuffle)
                    for i, p in enumerate(players_to_shuffle):
                        assigned_team = 'A' if i % 2 == 0 else 'B'
                        conn.table("participants").update({"team": assigned_team}).eq("id", p['id']).execute()
                    st.success("Teams split! Check the Pitch tab.")
                    st.rerun()
                
                if any(p.get('team') for p in main_squad):
                    team_a = [p['nom_complet'] for p in main_squad if p.get('team') == 'A']
                    team_b = [p['nom_complet'] for p in main_squad if p.get('team') == 'B']
                    summary = f"⚽ *Teams:* \n\n*🔵 Team A:* {', '.join(team_a)}\n\n*🔴 Team B:* {', '.join(team_b)}"
                    share_url = f"https://wa.me/?text={summary.replace(' ', '%20').replace('\\n', '%0A')}"
                    st.markdown(f'<a href="{share_url}" target="_blank" class="wa-btn">📲 Share Teams on WhatsApp</a>', unsafe_allow_html=True)
            else:
                st.info("Wait for 10 players to generate teams.")

            st.divider()
            st.subheader("📢 WhatsApp Reminders")
            for j in main_squad:
                if j.get('phone'):
                    msg = f"⚽ Match Reminder: Today at {match['heure']}! See you there."
                    wa_url = f"https://wa.me/{j['phone']}?text={msg.replace(' ', '%20')}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">Ping {j["nom_complet"]}</a>', unsafe_allow_html=True)

            st.divider()
            with st.expander("🏁 Archive & Record Score"):
                with st.form("score"):
                    sa, sb = st.number_input("Team A", 0), st.number_input("Team B", 0)
                    if st.form_submit_button("Finish Match"):
                        conn.table("matches").update({"score_a": sa, "score_b": sb, "is_finished": True}).eq("id", match['id']).execute()
                        st.rerun()

            st.subheader("Manage Players")
            for j in joueurs:
                c1, c2 = st.columns([3, 1])
                c1.write(j['nom_complet'])
                if c2.button("❌", key=f"k_{j['id']}"):
                    conn.table("participants").delete().eq("id", j['id']).execute()
                    st.rerun()
        else:
            st.info("Admin password required.")

    with t4:
        st.subheader("Recent Results")
        for hm in history:
            st.write(f"📅 {hm['date']} | Team A {hm['score_a']} - {hm['score_b']} Team B")

else:
    st.info("No active match. Create one in the sidebar.")

if is_admin:
    with st.sidebar.expander("🆕 Create Match"):
        d = st.date_input("Date")
        h1, h2 = st.time_input("Start"), st.time_input("End")
        l, m = st.text_input("Stadium"), st.text_input("Maps Link")
        if st.button("Publish"):
            conn.table("matches").insert({"date": str(d), "heure": str(h1), "heure_fin": str(h2), "lieu": l, "maps_url": m, "is_finished": False}).execute()
            st.rerun()
