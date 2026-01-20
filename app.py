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

# --- CSS STYLE ---
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
    .match-card { background: white; padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 10px;}
    .history-card { background: #f1f3f4; padding: 10px; border-radius: 10px; margin-bottom: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
def get_data():
    # Active Match
    m = conn.table("matches").select("*").eq("is_finished", False).order("id", desc=True).limit(1).execute()
    match_data = m.data[0] if m.data else None
    
    # Finished Matches (History)
    h = conn.table("matches").select("*").eq("is_finished", True).order("date", desc=True).limit(5).execute()
    
    joueurs_data = []
    if match_data:
        p = conn.table("participants").select("*").eq("match_id", match_data['id']).order("created_at").execute()
        joueurs_data = p.data if p.data else []
    
    return match_data, joueurs_data, h.data

match, joueurs, history = get_data()

# --- DURATION & LIMIT LOGIC ---
limite_joueurs = 10
if match and match.get('heure_fin') and match.get('heure'):
    try:
        fmt = '%H:%M:%S' if len(match['heure']) > 5 else '%H:%M'
        delta = (datetime.strptime(match['heure_fin'], fmt) - datetime.strptime(match['heure'], fmt)).total_seconds() / 3600
        limite_joueurs = 12 if delta > 1 else 10
    except: pass

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
        <h3>📅 Next Match: {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> | 📍 {match['lieu']}</p>
        <p>👥 <b>{len(main_squad)} / {limite_joueurs} Players</b> (+{len(waiting_list)} waiting)</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📋 Register", "🏟️ Pitch", "⚙️ Admin", "📜 History"])

    with t1:
        st.link_button("🗺️ Location", match['maps_url'], use_container_width=True)
        if len(main_squad) >= limite_joueurs:
            st.warning("Squad is full. You will be added to the WAITING LIST.")
        with st.form("reg"):
            n = st.text_input("Name")
            p = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
            if st.form_submit_button("Join Squad"):
                if n:
                    conn.table("participants").insert({"match_id": match['id'], "nom_complet": n, "poste": p, "statut": "Confirmed ✅"}).execute()
                    st.rerun()

    with t2:
        st.subheader("Starting Lineup")
        pitch_html = '<div class="pitch-container">'
        y_map = {"Forward": 18, "Midfielder": 42, "Defender": 68, "Goalkeeper": 88}
        for pos_name, y_top in y_map.items():
            at_pos = [j for j in main_squad if j['poste'] == pos_name]
            for i, p in enumerate(at_pos):
                x_left = (100 / (len(at_pos) + 1)) * (i + 1)
                pitch_html += f'<div class="player-label" style="top:{y_top}%; left:{x_left}%;">{p["nom_complet"]}</div>'
        st.markdown(pitch_html + '</div>', unsafe_allow_html=True)

    with t3:
        if is_admin:
            with st.expander("📝 Update Match Details"):
                with st.form("edit"):
                    u_l = st.text_input("Location", value=match['lieu'])
                    u_h = st.text_input("Time", value=match['heure'])
                    if st.form_submit_button("Save"):
                        conn.table("matches").update({"lieu": u_l, "heure": u_h}).eq("id", match['id']).execute()
                        st.rerun()
            
            with st.expander("🏁 End Match & Record Score"):
                with st.form("score"):
                    s_a = st.number_input("Team A", step=1)
                    s_b = st.number_input("Team B", step=1)
                    if st.form_submit_button("Finish Match"):
                        conn.table("matches").update({"score_a": s_a, "score_b": s_b, "is_finished": True}).eq("id", match['id']).execute()
                        st.rerun()

            st.subheader("Kick Players")
            for j in joueurs:
                c1, c2 = st.columns([3, 1])
                c1.write(j['nom_complet'])
                if c2.button("❌", key=f"k_{j['id']}"):
                    conn.table("participants").delete().eq("id", j['id']).execute()
                    st.rerun()
        else:
            st.info("Enter admin code in sidebar.")

    with t4:
        st.subheader("Recent Results")
        for h_match in history:
            st.markdown(f"""
            <div class="history-card">
                <b>{h_match['date']}</b>: Team A {h_match['score_a']} - {h_match['score_b']} Team B
            </div>
            """, unsafe_allow_html=True)

if is_admin:
    with st.sidebar.expander("🆕 New Match"):
        d = st.date_input("Date")
        h1 = st.time_input("Start")
        h2 = st.time_input("End")
        l = st.text_input("Stadium")
        m = st.text_input("Maps Link")
        if st.button("Publish"):
            conn.table("matches").insert({"date": str(d), "heure": str(h1), "heure_fin": str(h2), "lieu": l, "maps_url": m, "is_finished": False}).execute()
            st.rerun()
