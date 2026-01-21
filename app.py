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
    
    .pitch-container {
        background-color: #1a472a;
        background-image: 
            repeating-linear-gradient(90deg, transparent, transparent 10%, rgba(255,255,255,0.05) 10%, rgba(255,255,255,0.05) 20%),
            linear-gradient(90deg, transparent 49.7%, rgba(255,255,255,0.8) 50%, transparent 50.3%),
            radial-gradient(circle at center, transparent 40px, rgba(255,255,255,0.8) 40px, rgba(255,255,255,0.8) 42px, transparent 42px);
        border: 4px solid rgba(255,255,255,0.9);
        height: 520px; width: 100%; position: relative; border-radius: 8px; margin-top: 20px; overflow: hidden;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
    }
    
    .pitch-container::before, .pitch-container::after {
        content: ""; position: absolute; top: 25%; height: 50%; width: 50px; border: 2px solid rgba(255,255,255,0.8);
    }
    .pitch-container::before { left: -2px; border-radius: 0 10px 10px 0; }
    .pitch-container::after { right: -2px; border-radius: 10px 0 0 10px; }

    .player-label {
        padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 12px;
        position: absolute; transform: translate(-50%, -50%); box-shadow: 0 4px 6px rgba(0,0,0,0.4); 
        white-space: nowrap; z-index: 100;
    }
    .team-a { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; border: 1.5px solid white; }
    .team-b { background: linear-gradient(135deg, #991b1b, #ef4444); color: white; border: 1.5px solid white; }
    .no-team { background: #f8fafc; color: #1e293b; border: 1px solid #94a3b8; }
    .wa-btn { background-color: #25D366; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
    is_admin = (pw == "foot!")
    
    if is_admin:
        st.divider()
        with st.expander("🆕 Create New Match", expanded=not match):
            d = st.date_input("Match Date")
            col1, col2 = st.columns(2)
            h_start = col1.text_input("Start Time", "20:00")
            h_end = col2.text_input("End Time", "21:00")
            l = st.text_input("Stadium Name")
            m_link = st.text_input("Google Maps Link")
            if st.button("Publish Match", use_container_width=True):
                conn.table("matches").insert({"date": str(d), "heure": h_start, "heure_fin": h_end, "lieu": l, "maps_url": m_link, "is_finished": False}).execute()
                st.rerun()

# --- MAIN UI ---
st.title("⚽ Hali Saha Pro")

if match:
    limite_joueurs = 10
    main_squad = joueurs[:limite_joueurs]
    reserve_list = joueurs[limite_joueurs:]
    
    st.markdown(f"""
    <div class="match-card">
        <h3>📅 Match: {match['date']}</h3>
        <p>⏱️ <b>{match['heure']} — {match.get('heure_fin', 'N/A')}</b> | 📍 {match['lieu']}</p>
        <p>👥 <b>{len(main_squad)} / {limite_joueurs} Players</b> (+{len(reserve_list)} reserve)</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3, t4 = st.tabs(["📋 Squad", "🏟️ Pitch", "⚙️ Admin", "📜 History"])

    with t1:
        st.link_button("🗺️ Open Location", match['maps_url'], use_container_width=True)
        st.subheader("Main Squad")
        for i, p in enumerate(main_squad):
            st.write(f"{i+1}. **{p['nom_complet']}** ({'⭐' * p.get('level', 3)})")
        
        if reserve_list:
            st.divider()
            st.subheader("Reserve List")
            for i, p in enumerate(reserve_list):
                st.write(f"{i+1}. {p['nom_complet']} (Waiting...)")

        with st.form("reg_form"):
            st.write("---")
            n = st.text_input("Full Name")
            col_p1, col_p2 = st.columns([1, 4])
            col_p1.text_input("Country", "+32", disabled=True)
            ph_raw = col_p2.text_input("Phone Number", placeholder="470123456")
            lvl = st.select_slider("Select Skill Level", options=[1, 2, 3, 4, 5], value=3)
            if st.form_submit_button("Join Match", use_container_width=True):
                if n:
                    clean = "".join(filter(str.isdigit, ph_raw)).lstrip('0')
                    if clean.startswith("32"): clean = clean[2:]
                    conn.table("participants").insert({"match_id": match['id'], "nom_complet": n, "phone": f"32{clean}", "level": lvl, "statut": "Confirmed ✅"}).execute()
                    st.rerun()
                else: st.error("Please enter a name.")

    with t2:
        pitch_html = '<div class="pitch-container">'
        formation_coords = [{"y": 88, "x": 50}, {"y": 65, "x": 22}, {"y": 65, "x": 78}, {"y": 25, "x": 22}, {"y": 25, "x": 78}]
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
            # 1. GROUP ANNOUNCEMENT (WITH PLAYERS & TEAMS)
            with st.expander("📢 Group Announcement", expanded=True):
                app_url = "https://matchorganizer.streamlit.app/" 
                
                # Build strings
                squad_text = "*📋 Main Squad:*\n"
                for i, p in enumerate(main_squad):
                    squad_text += f"{i+1}. {p['nom_complet']}\n"
                
                team_text = ""
                t_a_names = [p['nom_complet'] for p in main_squad if p.get('team') == 'A']
                t_b_names = [p['nom_complet'] for p in main_squad if p.get('team') == 'B']
                if t_a_names or t_b_names:
                    team_text = f"\n*🔵 Team A:* {', '.join(t_a_names)}\n*🔴 Team B:* {', '.join(t_b_names)}\n"

                res_text = ""
                if reserve_list:
                    res_text = "\n*⏳ Reserve List:*\n"
                    for p in reserve_list:
                        res_text += f"- {p['nom_complet']}\n"

                full_msg = (
                    f"⚽ *HALI SAHA MATCH SHEET*\n\n"
                    f"📅 *Date:* {match['date']}\n"
                    f"⏰ *Time:* {match['heure']} - {match.get('heure_fin', 'N/A')}\n"
                    f"📍 *Lieu:* {match['lieu']}\n"
                    f"{team_text}"
                    f"{squad_text}"
                    f"{res_text}\n"
                    f"📝 *Join/View:* {app_url}"
                )
                
                encoded_msg = full_msg.replace(" ", "%20").replace("\n", "%0A")
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank" class="wa-btn" style="background-color:#128C7E;">📢 Share Full Match Sheet</a>', unsafe_allow_html=True)

            # 2. BULK IMPORT & LEVEL EDIT
            with st.expander("📥 Bulk Import & Edit Levels"):
                bulk_input = st.text_area("Paste Names (One per line)", height=100)
                if st.button("Import", use_container_width=True):
                    for line in bulk_input.split('\n'):
                        name = "".join(filter(lambda x: not x.isdigit(), line)).replace(".", "").strip()
                        if name: conn.table("participants").insert({"match_id": match['id'], "nom_complet": name, "level": 3}).execute()
                    st.rerun()
                
                st.write("---")
                st.write("Edit Player Levels:")
                for j in joueurs:
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(j['nom_complet'])
                    new_lvl = c2.select_slider("Lvl", [1,2,3,4,5], value=j.get('level', 3), key=f"ed_{j['id']}")
                    if new_lvl != j.get('level'):
                        conn.table("participants").update({"level": new_lvl}).eq("id", j['id']).execute()
                        st.rerun()
                    if c3.button("❌", key=f"del_{j['id']}"):
                        conn.table("participants").delete().eq("id", j['id']).execute()
                        st.rerun()

            # 3. BALANCING
            with st.expander("⚖️ Team Organization"):
                if st.button("🔀 Balance Teams (Snake Draft)", use_container_width=True):
                    sorted_p = sorted(main_squad, key=lambda x: x.get('level', 3), reverse=True)
                    assign = ['A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', 'B']
                    for i, p in enumerate(sorted_p):
                        if i < len(assign): conn.table("participants").update({"team": assign[i]}).eq("id", p['id']).execute()
                    st.rerun()
                
                if st.button("🗑️ Clear Teams", type="secondary", use_container_width=True):
                    conn.table("participants").update({"team": None}).eq("match_id", match['id']).execute()
                    st.rerun()

            with st.expander("🗑️ Danger Zone"):
                if st.button("Delete Match", type="primary"):
                    conn.table("participants").delete().eq("match_id", match['id']).execute()
                    conn.table("matches").delete().eq("id", match['id']).execute()
                    st.rerun()
        else: st.info("Admin access required.")

    with t4:
        for hm in history: st.write(f"📅 {hm['date']} | {hm['score_a']} - {hm['score_b']}")
else:
    st.info("No active match.")
