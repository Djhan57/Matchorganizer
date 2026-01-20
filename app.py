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

# --- CSS STYLE (With Split Pitch Middle Line) ---
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
            linear-gradient(90deg, transparent 49.5%, var(--pitch-line) 50%, transparent 50.5%), /* Middle Line */
            radial-gradient(circle at center, transparent 0, transparent 40px, var(--pitch-line) 40px, var(--pitch-line) 42px, transparent 42px);
        background-size: 100% 50%, 50% 100%, 100% 100%, 100% 100%;
        border: 3px solid var(--pitch-line); height: 500px; width: 100%; position: relative; border-radius: 10px; margin-top: 20px; overflow: hidden;
    }
    .player-label {
        padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); white-space: nowrap; z-index: 100;
    }
    .team-a { background: #3b82f6 !important; color: white !important; border: 2px solid white !important; }
    .team-b { background: #ef4444 !important; color: white !important; border: 2px solid white !important; }
    .no-team { background: white !important; color: black !important; border: 1px solid #2e7d32 !important; }
    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
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
        <h3>📅 Match: {match['date']}</h3>
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
                    clean_digits = "".join(filter(str.isdigit, ph_raw)).lstrip('0')
                    if clean_digits.startswith("32"): clean_digits = clean_digits[2:]
                    final_phone = f"32{clean_digits}"
                    confirm_registration(n, final_phone, p, match['id'], len(main_squad) >= limite_joueurs)
                else: st.error("Fields missing.")

    with t2:
        st.subheader("Tactical Lineup")
        pitch_html = '<div class="pitch-container">'
        y_map = {"Forward": 18, "Midfielder": 42, "Defender": 68, "Goalkeeper": 88}
        
        team_a_p = [p for p in main_squad if p.get('team') == 'A']
        team_b_p = [p for p in main_squad if p.get('team') == 'B']
        others = [p for p in main_squad if p.get('team') not in ['A', 'B']]

        def add_p(p_list, side):
            h = ""
            for pos_name, y_top in y_map.items():
                at_pos = [j for j in p_list if j['poste'] == pos_name]
                for i, p in enumerate(at_pos):
                    if side == "left": x = (50 / (len(at_pos) + 1)) * (i + 1); t_cl = "team-a"
                    elif side == "right": x = 50 + (50 / (len(at_pos) + 1)) * (i + 1); t_cl = "team-b"
                    else: x = 50; t_cl = "no-team"
                    h += f'<div class="player-label {t_cl}" style="top:{y_top}%; left:{x}%;">{p["nom_complet"]}</div>'
            return h

        pitch_html += add_p(team_a_p, "left")
        pitch_html += add_p(team_b_p, "right")
        pitch_html += add_p(others, "center")
        st.markdown(pitch_html + '</div>', unsafe_allow_html=True)

    with t3:
        if is_admin:
            st.subheader("🛠️ Admin Tools")
            col_gen, col_clear = st.columns(2)
            if len(main_squad) >= 10:
                if col_gen.button("🔀 Generate Teams"):
                    shuffled = main_squad.copy()
                    random.shuffle(shuffled)
                    for i, p in enumerate(shuffled):
                        t = 'A' if i % 2 == 0 else 'B'
                        conn.table("participants").update({"team": t}).eq("id", p['id']).execute()
                    st.rerun()
                if col_clear.button("🗑️ Clear Teams"):
                    conn.table("participants").update({"team": None}).eq("match_id", match['id']).execute()
                    st.rerun()

            st.divider()
            with st.expander("🏁 Archive Match"):
                with st.form("score"):
                    sa, sb = st.number_input("Team A", 0), st.number_input("Team B", 0)
                    if st.form_submit_button("Save & Close"):
                        conn.table("matches").update({"score_a": sa, "score_b": sb, "is_finished": True}).eq("id", match['id']).execute()
                        st.rerun()

            st.subheader("⚠️ Danger Zone")
            if st.checkbox("Confirm Deletion"):
                if st.button("Delete Match Entirely", type="primary"):
                    conn.table("participants").delete().eq("match_id", match['id']).execute()
                    conn.table("matches").delete().eq("id", match['id']).execute()
                    st.rerun()
        else: st.info("Password needed.")

    with t4:
        for hm in history: st.write(f"📅 {hm['date']} | A {hm['score_a']} - {hm['score_b']} B")
else:
    st.info("No active match.")

if is_admin:
    with st.sidebar.expander("🆕 New Match"):
        d = st.date_input("Date")
        l, m = st.text_input("Stadium"), st.text_input("Maps Link")
        if st.button("Create"):
            conn.table("matches").insert({"date": str(d), "heure": "20:00", "lieu": l, "maps_url": m, "is_finished": False}).execute()
            st.rerun()
