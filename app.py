import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Hali Saha Pro", page_icon="⚽", layout="centered")

try:
    # On essaie d'abord la méthode automatique
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    # Si ça échoue, on force avec les paramètres manuels
    url = st.secrets.get("SUPABASE_URL") or st.secrets["connections"]["supabase"]["url"]
    key = st.secrets.get("SUPABASE_KEY") or st.secrets["connections"]["supabase"]["key"]
    conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- SMART DARK MODE & UI CSS ---
st.markdown("""
    <style>
    :root {
        --card-bg: #ffffff;
        --card-text: #1e2d24;
        --pitch-line: white;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --card-bg: #1e1e1e;
            --card-text: #ffffff;
            --pitch-line: rgba(255,255,255,0.6);
        }
        .stApp { background-color: #0e1117; }
    }

    .match-card { 
        background-color: var(--card-bg); 
        color: var(--card-text);
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
        background: white; color: black; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); border: 1px solid #2e7d32; white-space: nowrap; z-index: 100;
    }

    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
def get_data():
    # Active Match (Not finished)
    m = conn.table("matches").select("*").eq("is_finished", False).order("id", desc=True).limit(1).execute()
    match_data = m.data[0] if m.data else None
    
    # History
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
    is_admin = (pw == "VOTRE_MOT_DE_PASSE") # UPDATE THIS

# --- UI LOGIC ---
st.title("⚽ Hali Saha Pro")

if match:
    # Squad Limits
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
        st.link_button("🗺️ Open Stadium Location", match['maps_url'], use_container_width=True)
        if len(main_squad) >= limite_joueurs:
            st.warning("You are joining the WAITING LIST.")
        with st.form("reg"):
            n = st.text_input("Full Name")
            ph = st.text_input("Phone (e.g. 33600000000)")
            p = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
            if st.form_submit_button("Join Match"):
                if n and ph:
                    conn.table("participants").insert({"match_id": match['id'], "nom_complet": n, "phone": ph, "poste": p, "statut": "Confirmed ✅"}).execute()
                    st.rerun()

    with t2:
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
            # THIS IS THE PART THAT WAS DISAPPEARING
            st.subheader("🛠️ Edit Match Info")
            with st.form("edit_active"):
                u_l = st.text_input("Location", value=match['lieu'])
                u_d = st.text_input("Date", value=str(match['date']))
                u_h = st.text_input("Start Time", value=match['heure'])
                u_f = st.text_input("End Time", value=match['heure_fin'])
                u_m = st.text_input("Maps URL", value=match['maps_url'])
                if st.form_submit_button("Update Current Match"):
                    conn.table("matches").update({"lieu": u_l, "date": u_d, "heure": u_h, "heure_fin": u_f, "maps_url": u_m}).eq("id", match['id']).execute()
                    st.success("Updated!")
                    st.rerun()

            st.divider()
            st.subheader("📢 Reminders")
            for j in main_squad:
                if j.get('phone'):
                    msg = f"⚽ Match Reminder: {match['heure']} at {match['lieu']}!"
                    wa_url = f"https://wa.me/{j['phone'].replace('+', '')}?text={msg.replace(' ', '%20')}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">Ping {j["nom_complet"]}</a>', unsafe_allow_html=True)

            st.divider()
            with st.expander("🏁 End Match & Save Score"):
                with st.form("score"):
                    sa, sb = st.number_input("Team A", 0), st.number_input("Team B", 0)
                    if st.form_submit_button("Record Result"):
                        conn.table("matches").update({"score_a": sa, "score_b": sb, "is_finished": True}).eq("id", match['id']).execute()
                        st.rerun()

            st.subheader("Manage Squad")
            for j in joueurs:
                c1, c2 = st.columns([3, 1])
                c1.write(f"{j['nom_complet']}")
                if c2.button("❌", key=f"k_{j['id']}"):
                    conn.table("participants").delete().eq("id", j['id']).execute()
                    st.rerun()
        else: st.info("Enter Admin Code in sidebar.")

    with t4:
        st.subheader("Recent Results")
        for h_m in history:
            st.write(f"📅 {h_m['date']} | Team A {h_m['score_a']} - {h_m['score_b']} Team B")
else:
    st.info("No active match. Create one in the sidebar!")

# --- ALWAYS SHOW NEW MATCH OPTION TO ADMIN ---
if is_admin:
    with st.sidebar.expander("🆕 Create New Match"):
        d = st.date_input("Date")
        h1, h2 = st.time_input("Start"), st.time_input("End")
        loc, maps = st.text_input("Stadium"), st.text_input("Maps Link")
        if st.button("Publish"):
            conn.table("matches").insert({"date": str(d), "heure": str(h1), "heure_fin": str(h2), "lieu": loc, "maps_url": maps, "is_finished": False}).execute()
            st.rerun()
