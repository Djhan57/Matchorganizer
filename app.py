import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Halı Saha Pro", page_icon="⚽", layout="centered")

# --- CONNEXION BASE DE DONNÉES ---
try:
    # Tente de se connecter via les Secrets Streamlit
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("⚠️ Erreur de connexion : Vérifiez vos Secrets Streamlit (URL et Key).")
    st.stop()

# --- STYLE CSS (Terrain et Joueurs) ---
st.markdown("""
    <style>
    .pitch {
        background-color: #2e7d32;
        border: 2px solid white;
        height: 400px;
        width: 100%;
        position: relative;
        border-radius: 15px;
        background-image: linear-gradient(rgba(255,255,255,.1) 50%, transparent 50%);
        background-size: 100% 40px;
        margin-bottom: 20px;
    }
    .player-card {
        background: white;
        color: black;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        position: absolute;
        transform: translateX(-50%);
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
        border: 1px solid #ccc;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS RÉCUPÉRATION DONNÉES ---
def get_latest_match():
    res = conn.table("matches").select("*").order("id", desc=True).limit(1).execute()
    return res.data[0] if res.data else None

def get_participants(match_id):
    res = conn.table("participants").select("*").eq("match_id", match_id).execute()
    return res.data if res.data else []

# Initialisation des données
match = get_latest_match()
joueurs = get_participants(match['id']) if match else []

# --- BARRE LATÉRALE (ADMIN) ---
st.sidebar.title("🔐 Espace Organisateur")
admin_key = st.sidebar.text_input("Code Admin", type="password")
is_admin = (admin_key == "VOTRE_MOT_DE_PASSE") # <--- CHANGEZ VOTRE CODE ICI

# --- INTERFACE PRINCIPALE ---
st.title("⚽ Halı Saha Pro")

if not match:
    st.warning("Aucun match n'est programmé pour le moment.")
    if not is_admin:
        st.stop()
else:
    # Tabs pour une navigation fluide sur mobile
    tab_match, tab_terrain, tab_admin = st.tabs(["📅 Match", "🏟️ Terrain", "🏗️ Admin"])

    # --- ONGLET 1 : INFOS ET INSCRIPTION ---
    with tab_match:
        st.header(f"Match du {match['date']}")
        col1, col2 = st.columns(2)
        col1.metric("⏰ Heure", match['heure'])
        col1.metric("📍 Lieu", match['lieu'])
        
        with col2:
            st.write("Retrouvez le stade ici :")
            st.link_button("🗺️ Google Maps", match['maps_url'], use_container_width=True)

        st.divider()
        
        st.subheader("📝 S'inscrire")
        with st.form("inscription_form"):
            nom = st.text_input("Prénom & Nom")
            poste = st.selectbox("Poste", ["Gardien", "Défenseur", "Milieu", "Attaquant"])
            statut = st.radio("Présence", ["Je viens ✅", "Absent ❌"], horizontal=True)
            
            if st.form_submit_button("Valider l'inscription", use_container_width=True):
                if nom:
                    new_player = {
                        "match_id": match['id'],
                        "nom_complet": nom,
                        "poste": poste,
                        "statut": statut
                    }
                    conn.table("participants").insert(new_player).execute()
                    st.success(f"Salut {nom}, c'est enregistré !")
                    st.rerun()
                else:
                    st.error("Veuillez entrer votre nom.")

    # --- ONGLET 2 : VISUALISATION DU TERRAIN ---
    with tab_terrain:
        presents = [j for j in joueurs if "✅" in j['statut']]
        st.subheader(f"Composition ({len(presents)} joueurs)")
        
        st.markdown('<div class="pitch">', unsafe_allow_html=True)
        
        coords = {
            "Gardien": {"top": "85%", "left": "50%"},
            "Défenseur": {"top": "65%", "left": "50%"},
            "Milieu": {"top": "40%", "left": "50%"},
            "Attaquant": {"top": "15%", "left": "50%"}
        }

        # Dictionnaire pour gérer les décalages si plusieurs joueurs au même poste
        offsets = {"Gardien": 0, "Défenseur": 0, "Milieu": 0, "Attaquant": 0}

        for j in presents:
            pos = coords.get(j['poste'], {"top": "50%", "left": "50%"})
            current_offset = offsets[j['poste']]
            left_val = f"calc({pos['left']} + {current_offset}px)"
            
            st.markdown(f'''
                <div class="player-card" style="top: {pos['top']}; left: {left_val};">
                    {j['nom_complet']}
                </div>
            ''', unsafe_allow_html=True)
            
            # Alterne le décalage pour ne pas superposer les noms
            offsets[j['poste']] = (current_offset + 60) if current_offset <= 0 else (current_offset * -1)

        st.markdown('</div>', unsafe_allow_html=True)
        
        # Liste textuelle en dessous pour plus de clarté
        if presents:
            with st.expander("Voir la liste complète"):
                for p in presents:
                    st.write(f"• {p['nom_complet']} ({p['poste']})")

    # --- ONGLET 3 : ADMINISTRATION ---
    with tab_admin:
        if is_admin:
            st.subheader("🛠️ Gestion du Match")
            
            # Modification des infos
            with st.form("edit_match"):
                u_date = st.text_input("Date", value=match['date'])
                u_heure = st.text_input("Heure", value=match['heure'])
                u_lieu = st.text_input("Lieu", value=match['lieu'])
                u_maps = st.text_input("Lien Maps", value=match['maps_url'])
                if st.form_submit_button("Mettre à jour les infos"):
                    conn.table("matches").update({"date": u_date, "heure": u_heure, "lieu": u_lieu, "maps_url": u_maps}).eq("id", match['id']).execute()
                    st.success("Modifications enregistrées !")
                    st.rerun()
            
            st.divider()
            
            # Suppression des joueurs
            st.subheader("👤 Liste des inscrits (Modération)")
            if joueurs:
                for j in joueurs:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{j['nom_complet']}** ({j['statut']})")
                    if c2.button("❌", key=f"del_{j['id']}"):
                        conn.table("participants").delete().eq("id", j['id']).execute()
                        st.rerun()
            else:
                st.info("Aucun inscrit.")
        else:
            st.info("Veuillez entrer le code admin dans le menu à gauche.")

# --- CRÉATION NOUVEAU MATCH (Toujours dispo pour l'admin) ---
if is_admin:
    with st.sidebar.expander("➕ Créer un nouveau match"):
        new_date = st.date_input("Date")
        new_time = st.time_input("Heure")
        new_place = st.text_input("Stade")
        new_link = st.text_input("Lien Google Maps")
        if st.button("Lancer ce match"):
            conn.table("matches").insert({
                "date": str(new_date), "heure": str(new_time), 
                "lieu": new_place, "maps_url": new_link
            }).execute()
            st.rerun()
