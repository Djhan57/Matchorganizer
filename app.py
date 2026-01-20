import streamlit as st
import pandas as pd  # <--- Vérifiez que cette ligne est bien présente
from st_supabase_connection import SupabaseConnection

# 1. Connexion à la base de données réelle
# Ces clés doivent être mises dans vos "Secrets" sur Streamlit Cloud
conn = st.connection("supabase", type=SupabaseConnection)

st.title("⚽ Halı Saha Pro")

# --- LOGIQUE DE RÉCUPÉRATION DU MATCH ---
def get_latest_match():
    res = conn.table("matches").select("*").order("id", desc=True).limit(1).execute()
    return res.data[0] if res.data else None

match = get_latest_match()

# --- INTERFACE UTILISATEUR ---
if match:
    st.header(f"Prochain Match : {match['date']}")
    st.info(f"🏟️ {match['lieu']} | ⏰ {match['heure']}")
    st.link_button("📍 Ouvrir Google Maps", match['maps_url'])

    with st.expander("📝 M'inscrire / Modifier ma présence"):
        with st.form("inscription"):
            nom = st.text_input("Prénom et Nom")
            poste = st.selectbox("Poste", ["Gardien", "Défenseur", "Milieu", "Attaquant"])
            statut = st.radio("Présence", ["Je viens ✅", "Absent ❌"])
            
            if st.form_submit_button("Confirmer"):
                data = {
                    "match_id": match['id'], 
                    "nom_complet": nom, 
                    "poste": poste, 
                    "statut": statut
                }
                conn.table("participants").insert(data).execute()
                st.success("C'est noté !")
                st.rerun()

    # --- AFFICHAGE DU TERRAIN ---
    st.subheader("Composition de l'équipe")
    participants_res = conn.table("participants").select("*").eq("match_id", match['id']).execute()
    joueurs = participants_res.data if participants_res.data else []
    
    # Filtrer uniquement ceux qui viennent
    presents = [j for j in joueurs if "✅" in j['statut']]
    
    if presents:
        df = pd.DataFrame(presents)
        st.table(df[['nom_complet', 'poste']])
    else:
        st.write("Aucun joueur inscrit pour le moment.")

else:
    st.warning("Aucun match n'est programmé pour le moment.")

# --- SECTION ADMIN (Protégée) ---
st.sidebar.divider()
admin_key = st.sidebar.text_input("Code Admin", type="password")
if admin_key == "VOTRE_MOT_DE_PASSE": # À personnaliser
    st.sidebar.success("Mode Admin activé")
    with st.sidebar.expander("➕ Créer un match"):
        d = st.date_input("Date")
        h = st.time_input("Heure")
        l = st.text_input("Lieu")
        m = st.text_input("Lien Maps")
        if st.button("Publier"):
            new_m = {"date": str(d), "heure": str(h), "lieu": l, "maps_url": m}
            conn.table("matches").insert(new_m).execute()
            st.rerun()
