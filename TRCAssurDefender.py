import streamlit as st

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Cotation TRC - Assur Defender", layout="wide")

# CSS personnalisé pour les titres de section et les sous-titres
st.markdown("""
<style>
    .section-title {
        color: #6A0DAD; /* Violet foncé */
        font-size: 24px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    .section-subtitle {
        color: #444444;
        font-size: 18px;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    .divider {
        border-bottom: 1px solid #e0e0e0;
        margin: 25px 0;
    }
    .metric-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        background-color: #f9f9f9;
        margin-bottom: 10px;
    }
    .metric-container-total {
        border: 2px solid #6A0DAD;
        border-radius: 8px;
        padding: 15px;
        background-color: #f5eefd;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# BARÈMES (Basés sur les images)
# =========================================================
TARIFS_BATIMENT = {
    "logement_commercial": {
        "A": {"12m": 1.10, "18m": 1.27},
        "B": {"12m": 1.27, "18m": 1.44},
    },
    "public_industriel": {
        "A": {"12m": 1.27, "18m": 1.61},
        "B": {"12m": 1.44, "18m": 1.78},
    },
}

TARIF_ASSAINISSEMENT = {"12m": 2.21, "18m": 2.55}
TARIF_ROUTES = {"12m": 1.78, "18m": 2.12}

# NOUVEAU: Options pour la structure (pour le selectbox)
STRUCTURE_OPTIONS = {
    "Type A (Béton armé/acier, portée < 10m)": "A",
    "Type B (Acier/précontraint, portée 10-15m)": "B",
}

# Coefficients de franchise basés sur les images
FRANCHISE_COEF = {
    "Normale (x1)": 1.0,
    "Multipliée par 2 (Rabais 7,5%)": 0.925, # 1 - 0.075
    "Multipliée par 5 (Rabais 15%)": 0.85,   # 1 - 0.15
    "Multipliée par 10 (Rabais 25%)": 0.75,  # 1 - 0.25
    "Divisée par 2 (Augmentation 25%)": 1.25,
}

# Paramètres RC (Taux / Minimum)
RC_PARAMS = {
    "Bâtiment": {"pct": 0.15, "min": 0.35},
    "Assainissement": {"pct": 0.20, "min": 0.40},
    "Route": {"pct": 0.20, "min": 0.40},
}

# NOUVEAU: Suppléments RC (basés sur les images)
RC_SUPPLEMENTS = {
    "trafic": {
        "Non applicable": 1.0,
        "Trafic faible (+15%)": 1.15,
        "Trafic moyen (+30%)": 1.30,
        "Trafic intense (+60%)": 1.60,
    },
    "proximite": {
        "Non applicable": 1.0,
        "< 50m (non mitoyen) (+30%)": 1.30,
        "de 50 à 100 m (+10%)": 1.10,
        "de 100 à 200 m (+5%)": 1.05,
    },
}

# =========================================================
# BARÈMES INSTALLATIONS ET ÉQUIPEMENTS DE CHANTIER (A21, A22)
# =========================================================

# Taux annuels pour grues à tour (en ‰)
TARIFS_GRUES_TOUR = {
    "< 30M": {
        "Classe 1": 8.5,
        "Classe 2": 11.05,
        "Classe 3": 13.06,
    },
    "> 30M": {
        "Classe 1": 10.2,
        "Classe 2": 12.75,
        "Classe 3": 15.3,
    }
}

# Taux annuels pour engins mobiles (en ‰)
TARIFS_ENGINS = {
    "Grue automobile": {
        "Classe 1": 12.75,
        "Classe 2": 17.0,
        "Classe 3": 21.25,
    },
    "Bulldozers, niveleuses, scrapers": {
        "Classe 1": 8.5,
        "Classe 2": 12.75,
        "Classe 3": 17.0,
    },
    "Chargeurs, dumpers": {
        "Classe 1": 8.5,
        "Classe 2": 12.75,
        "Classe 3": 17.0,
    },
    "Compacteurs vibrants": {
        "Classe 1": 8.5,
        "Classe 2": 10.2,
        "Classe 3": 12.75,
    },
    "Sonnettes / extracteurs de pieux": {
        "Classe 1": 10.2,
        "Classe 2": 12.75,
        "Classe 3": 15.3,
    },
    "Rouleaux compresseurs": {
        "Classe 1": 8.5,
        "Classe 2": 10.2,
        "Classe 3": 12.75,
    },
    "Locomotives de chantier": {
        "Classe 1": 5.1,
        "Classe 2": 6.8,
        "Classe 3": 8.5,
    },
}

# Taux pour baraquements provisoires (en ‰)
TARIFS_BARAQUEMENTS = {
    "Baraquement de stockage": 4.5,
    "Bureaux provisoires de chantier": 4.0,
}

# Coefficients de durée (% du taux annuel)
COEF_DUREE_EQUIPEMENTS = {
    1: 0.45,
    2: 0.50,
    3: 0.55,
    4: 0.60,
    5: 0.65,
    6: 0.70,
    7: 0.75,
    8: 0.80,
    9: 0.85,
    10: 0.90,
    11: 0.95,
    12: 1.00,
}

# Rabais franchise pour équipements (franchise supérieure à 10% mini 500K)
RABAIS_FRANCHISE_EQUIPEMENTS = {
    "10% mini 500 000 FCFA (standard)": 1.0,
    "10% mini 1 000 000 FCFA (Rabais 5%)": 0.95,
    "10% mini 2 000 000 FCFA (Rabais 10%)": 0.90,
    "10% mini 5 000 000 FCFA (Rabais 15%)": 0.85,
    "10% mini 10 000 000 FCFA (Rabais 25%)": 0.75,
    "Franchise divisée par 2 (Majoration 25%)": 1.25,
}

# NOUVEAU: Dictionnaire des clauses
CLAUSES = {
    "obligatoires": {
        "Bâtiment": [
            "C01 : Installations de lutte contre les incendies",
            "B03 : Conduits Câbles Souterrains",
            "C06 : Conditions spéciales (pluies, ruissellements, inondations)",
        ],
        "Assainissement": [
            "B03 : Conduits Câbles Souterrains",
            "B05 : Dommages Récoltes Forêts Cultures",
            "C06 : Conditions spéciales (pluies, ruissellements, inondations)",
            "B09 : Travaux en tranchées",
            "Clause 117 : Conduites d'eau et égouts",
        ],
        "Route": [
            "B03 : Conduits Câbles Souterrains",
            "B05 : Dommages Récoltes Forêts Cultures",
            "C06 : Conditions spéciales (pluies, ruissellements, inondations)",
            "B09 : Travaux en tranchées",
        ],
    },
    "extensions": {
        "A05": "Maintenance visite (clause A05)",
        "A06": "Maintenance étendue (clause A06)",
        "A07": "Maintenance constructeur (clause A07)",
        "A17": "Responsabilité Civile Croisée (clause A17)",
        "A20": "Garantie des biens adjacents / existants (clause A20)",
        "A21": "Garantie du matériel et des engins de chantier (clause A21)",
        "A22": "Garantie des Baraquements et Entrepôts (clause A22)",
        "FANAF01": "Grèves, émeutes et mouvements populaires (clause FANAF 01)",
    }
}

# =========================================================
# FONCTIONS DE CALCUL
# =========================================================
def duree_key(duree):
    """Retourne la clé '12m' ou '18m' selon la durée."""
    return "12m" if duree <= 12 else "18m"

def calc_prime(montant, taux_millieme):
    """Calcule la prime basée sur un montant et un taux pour mille (‰)."""
    return montant * taux_millieme / 1000

def get_taux_base(type_travaux, duree, usage_key=None, structure=None):
    """Récupère le taux de base pour mille (‰) selon le type de travaux."""
    if type_travaux == "Bâtiment":
        if not usage_key or not structure:
            st.error("Usage et structure requis pour Bâtiment.")
            return 0
        return TARIFS_BATIMENT[usage_key][structure][duree_key(duree)]
    elif type_travaux == "Assainissement":
        return TARIF_ASSAINISSEMENT[duree_key(duree)]
    elif type_travaux == "Route":
        return TARIF_ROUTES[duree_key(duree)]
    return 0

# MODIFIÉ: Ajout des suppléments RC
def calc_taux_rc(type_travaux, taux_travaux, suppl_trafic_key, suppl_proximite_key, rc_croisee=False):
    """Calcule le taux RC final (‰) incluant les suppléments."""
    base = RC_PARAMS[type_travaux]
    
    # 1. Taux RC de base (min 0.35‰ ou 0.40‰)
    taux_rc = max(taux_travaux * base["pct"], base["min"])
    
    # 2. Application des suppléments (trafic, proximité)
    taux_rc *= RC_SUPPLEMENTS["trafic"][suppl_trafic_key]
    taux_rc *= RC_SUPPLEMENTS["proximite"][suppl_proximite_key]
    
    # 3. Application surprime RC Croisée (A17)
    if rc_croisee:
        taux_rc *= 1.20 # +20% sur le taux RC déjà calculé
        
    return taux_rc

def calc_accessoires(prime_nette):
    """Calcule les frais accessoires selon le barème."""
    if prime_nette <= 100_000: return 5_000
    if prime_nette <= 500_000: return 7_500
    if prime_nette <= 1_000_000: return 10_000
    if prime_nette <= 5_000_000: return 15_000
    if prime_nette <= 10_000_000: return 20_000
    if prime_nette <= 50_000_000: return 30_000
    return 50_000

def calc_taxes(prime_nette, accessoires, taux=0.145):
    """Calcule les taxes (TVA) sur la prime nette + accessoires."""
    return (prime_nette + accessoires) * taux

# =========================================================
# FONCTIONS DE CALCUL - ÉQUIPEMENTS ET INSTALLATIONS
# =========================================================
def get_coef_duree_equipement(duree_mois):
    """Retourne le coefficient de durée pour les équipements."""
    if duree_mois <= 12:
        return COEF_DUREE_EQUIPEMENTS.get(duree_mois, 1.0)
    else:
        # Si > 12 mois, proratiser (durée/12)
        return duree_mois / 12.0

def calc_prime_equipement(valeur, taux_annuel, duree_mois, coef_franchise):
    """
    Calcule la prime pour un équipement.
    Prime = Valeur × Taux annuel × Coef durée × Coef franchise
    """
    coef_duree = get_coef_duree_equipement(duree_mois)
    prime = valeur * (taux_annuel / 1000) * coef_duree * coef_franchise
    return prime

def get_taux_grue_tour(valeur, classe_chantier):
    """Retourne le taux annuel (‰) pour une grue à tour."""
    if valeur < 30_000_000:
        return TARIFS_GRUES_TOUR["< 30M"][classe_chantier]
    else:
        return TARIFS_GRUES_TOUR["> 30M"][classe_chantier]

def get_taux_engin(type_engin, classe_chantier):
    """Retourne le taux annuel (‰) pour un engin mobile."""
    return TARIFS_ENGINS.get(type_engin, {}).get(classe_chantier, 0)

def get_taux_baraquement(type_baraquement):
    """Retourne le taux annuel (‰) pour un baraquement."""
    return TARIFS_BARAQUEMENTS.get(type_baraquement, 0)

# =========================================================
# INTERFACE UTILISATEUR (UI)
# =========================================================
st.title("ASSUR DEFENDER – Tous Risques Chantier (TRC)")
st.markdown("---")

# ---------------------------------------------------------
# 1. Informations du projet et des intervenants
# ---------------------------------------------------------
st.markdown('<div class="section-title">Informations du projet et des intervenants</div>', unsafe_allow_html=True)

# Sous-section: Informations contractuelles
st.markdown('<div class="section-subtitle">Informations contractuelles</div>', unsafe_allow_html=True)
col_info1, col_info2 = st.columns(2)
souscripteur = col_info1.text_input("Souscripteur", key="souscripteur")
proposant = col_info2.text_input("Proposant", key="proposant")
intermediaire = col_info1.text_input("Intermédiaire", key="intermediaire")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Sous-section: Intervenants du projet
st.markdown('<div class="section-subtitle">Intervenants du projet</div>', unsafe_allow_html=True)
col_int1, col_int2 = st.columns(2)
entreprise_principale = col_int1.text_input("Entreprise Principale", key="entreprise_principale")
maitre_ouvrage = col_int2.text_input("Maître d'ouvrage", key="maitre_ouvrage")
maitrise_oeuvre = col_int1.text_input("Maîtrise d'œuvre", key="maitrise_oeuvre")
bureau_controle = col_int2.text_input("Bureau de Contrôle Technique", key="bureau_controle")
bureau_etude = col_int1.text_input("Bureau d'étude", key="bureau_etude")
labo_geotechnique = col_int2.text_input("Laboratoire d'Étude géotechnique", key="labo_geotechnique")
autres_intervenants = st.text_area("Autres Intervenants", key="autres_intervenants", height=80)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Sous-section: Description du projet
st.markdown('<div class="section-subtitle">Description du projet</div>', unsafe_allow_html=True)
col_desc1, col_desc2 = st.columns(2)
nature_travaux = col_desc1.text_area("Nature des travaux", key="nature_travaux", height=100)
situation_geo = col_desc2.text_area("Situation géographique", key="situation_geo", height=100)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Sous-section: Calendrier et périodes
st.markdown('<div class="section-subtitle">Calendrier du projet</div>', unsafe_allow_html=True)
col_cal1, col_cal2, col_cal3 = st.columns(3)
debut_travaux = col_cal1.date_input("Début des travaux", key="debut_travaux")
fin_travaux = col_cal2.date_input("Fin des travaux", key="fin_travaux")
# Calcul automatique de la durée en mois si les deux dates sont renseignées
if debut_travaux and fin_travaux:
    duree_calculee = (fin_travaux.year - debut_travaux.year) * 12 + (fin_travaux.month - debut_travaux.month)
    if duree_calculee < 0:
        duree_calculee = 0
    col_cal3.metric("Durée calculée", f"{duree_calculee} mois")
else:
    duree_calculee = None

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Sous-section: Maintenance et Essais
st.markdown('<div class="section-subtitle">Maintenance et Essais</div>', unsafe_allow_html=True)
col_maint1, col_maint2 = st.columns(2)
maintenance_incluse = col_maint1.checkbox("Maintenance incluse", key="maintenance_incluse")
if maintenance_incluse:
    periode_maintenance = col_maint2.text_input("Période de maintenance", key="periode_maintenance", 
                                                  placeholder="Ex: 12 mois à compter de la réception")
else:
    periode_maintenance = ""

col_essai1, col_essai2 = st.columns(2)
essai_inclus = col_essai1.checkbox("Essai inclus", key="essai_inclus")
if essai_inclus:
    periode_essai = col_essai2.text_input("Période d'essai", key="periode_essai",
                                           placeholder="Ex: 3 mois")
else:
    periode_essai = ""

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Informations générales (tarifaires)
# ---------------------------------------------------------
st.markdown('<div class="section-title">Informations tarifaires</div>', unsafe_allow_html=True)

# Option de tarification manuelle volontaire au début
tarif_manuel_volontaire = st.checkbox("Appliquer une tarification manuelle (hors barème)", key="tarif_volontaire_debut")

g1, g2 = st.columns([1, 2])
type_travaux = g1.selectbox("Type de travaux", ["Bâtiment", "Assainissement", "Route"], key="type_travaux")
# Montant par défaut à 0
montant = g1.number_input("Montant du chantier (Valeur à assurer)", min_value=0, value=0, step=10_000_000, format="%d")
# Utiliser la durée calculée si disponible, sinon 12 par défaut
duree_defaut = duree_calculee if duree_calculee is not None and duree_calculee > 0 else 12
duree = g2.number_input("Durée prévisionnelle (en mois)", min_value=1, value=duree_defaut, step=1, 
                        help="Cette durée sera utilisée pour le calcul tarifaire")
franchise_key = g2.selectbox("Franchise de base retenue", list(FRANCHISE_COEF.keys()))

# Vérification du dépassement de 2 milliards
depasse_limite = montant > 2_000_000_000
mode_manuel = False
raison_manuel = None  # Peut être: "montant_eleve", "validation_dt", ou "volontaire"

if tarif_manuel_volontaire:
    mode_manuel = True
    raison_manuel = "volontaire"
    st.info("ℹ️ **Mode tarification manuelle activé.** Vous pourrez saisir vos montants à la fin du parcours.")
elif depasse_limite:
    st.warning("⚠️ **Le montant du chantier dépasse la limite de 2 milliards FCFA.** Vous devrez saisir les primes manuellement à la fin du parcours.")
    mode_manuel = True
    raison_manuel = "montant_eleve"

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Paramètres spécifiques
# ---------------------------------------------------------
st.markdown('<div class="section-title">Paramètres tarifaires spécifiques</div>', unsafe_allow_html=True)

usage_key = None
structure = None

if type_travaux == "Bâtiment":
    p1, p2 = st.columns(2)
    usage_label = p1.selectbox(
        "Usage du bâtiment",
        [
            "Logements / bureaux / hôtels / magasins (max R+4)",
            "Usage public / industriel / écoles / usines",
        ],
    )
    usage_key = (
        "logement_commercial"
        if "Logements" in usage_label
        else "public_industriel"
    )
    # MODIFICATION: Remplacement de st.radio par st.selectbox
    structure_label = p2.selectbox(
        "Type de structure",
        list(STRUCTURE_OPTIONS.keys())
    )
    structure = STRUCTURE_OPTIONS[structure_label]
else:
    st.info("Ce type de travaux n'a pas de sous-paramètre (usage/structure).")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. Données techniques & Éligibilité
# ---------------------------------------------------------
st.markdown('<div class="section-title">Éligibilité du chantier</div>', unsafe_allow_html=True)
st.write("Veuillez confirmer que le chantier respecte les conditions du barème.")

# --- NOUVELLE REORGANISATION (Grille de 2 colonnes) ---
cond_montant = montant <= 2_000_000_000

# Initialiser les conditions spécifiques
cond_fondations = "Oui"
cond_sol_difficile = "Oui"
cond_inondation = "Oui"

# Créer une grille de 2 colonnes pour tous les Criteres
c1, c2 = st.columns(2)

# Criteres Communs
cond_maintenance_12m = c1.radio("Période de maintenance ≤ 12 mois ?", ["Oui", "Non"], horizontal=True, index=0)
cond_interruption = c2.radio("Reprise après interruption ?", ["Non", "Oui"], horizontal=True, index=0)
cond_proc_habituels = c1.radio("Procédés habituels ?", ["Oui", "Non"], horizontal=True, index=0)

# Criteres Spécifiques (placés dans la colonne 2 ou 1 pour équilibrer)
if type_travaux == "Bâtiment":
    cond_fondations = c2.radio("Réhabilitation SANS travaux sur fondations ?", ["Oui", "Non"], horizontal=True, index=0)
    cond_sol_difficile = c1.radio("Absence de conditions de sol difficiles (nappe, pieux) ?", ["Oui", "Non"], horizontal=True, index=0)
elif type_travaux == "Route":
    cond_sol_difficile = c2.radio("Absence de conditions de sol difficiles (nappe, fondations profondes) ?", ["Oui", "Non"], horizontal=True, index=0)
elif type_travaux == "Assainissement":
    cond_inondation = c2.radio("Travaux PEU exposés aux inondations ?", ["Oui", "Non"], horizontal=True, index=0)

# Vérification des alertes (logique mise à jour pour correspondre aux variables)
alerts = []
# Ne pas ajouter d'alerte pour le montant si on est déjà en mode manuel (> 2 Mds)
if not cond_montant and not mode_manuel:
    alerts.append(f"Montant ({montant:,.0f} FCFA) > 2 Mds FCFA")
if cond_maintenance_12m == "Non":
    alerts.append("Maintenance > 12 mois")
if cond_interruption == "Oui":
    alerts.append("Reprise après interruption")
if cond_proc_habituels == "Non":
    alerts.append("Procédés non-habituels")

if type_travaux == "Bâtiment":
    if cond_fondations == "Non":
        alerts.append("Travaux sur fondations (existantes/nouvelles)")
    if cond_sol_difficile == "Non":
        alerts.append("Conditions de sol difficiles (nappe, pieux, parois)")
elif type_travaux == "Route":
    if cond_sol_difficile == "Non":
        alerts.append("Conditions de sol difficiles (nappe, fondations profondes)")
elif type_travaux == "Assainissement":
    if cond_inondation == "Non":
        alerts.append("Travaux exposés aux inondations")

if alerts:
    st.error("⚠️ **Dossier à soumettre à la Direction Technique pour dérogation/tarification :**\n• " + "\n• ".join(alerts))
    # Proposer le mode manuel pour ces cas également
    continuer_avec_dt = st.checkbox("La Direction Technique a validé le dossier et fourni une tarification manuelle", key="continuer_dt")
    if continuer_avec_dt:
        mode_manuel = True
        raison_manuel = "validation_dt"
else:
    st.success("✅ **Chantier éligible à la tarification du barème.**")



st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Documents requis
# ---------------------------------------------------------
st.markdown('<div class="section-title">Documents requis</div>', unsafe_allow_html=True)

d1, d2, d3 = st.columns(3)
doc1 = d1.file_uploader("Questionnaire TRC", type=["pdf", "doc", "docx"], key="doc1")
doc2 = d2.file_uploader("CCTP (Cahier des clauses techniques)", type=["pdf", "doc", "docx"], key="doc2")
doc3 = d3.file_uploader("Descriptif technique des travaux", type=["pdf", "doc", "docx"], key="doc3")

d4, d5, d6 = st.columns(3)
doc4 = d4.file_uploader("Rapport d'étude de sol", type=["pdf", "doc", "docx"], key="doc4")
doc5 = d5.file_uploader("Planning des travaux", type=["pdf", "doc", "docx", "xlsx", "xls", "mpp"], key="doc5")
if type_travaux == "Route":
    doc6 = d6.file_uploader("Ouvrages d'art (caractéristiques et coût)", type=["pdf", "doc", "docx", "xlsx", "xls"], key="doc6")
else:
    doc6 = None

manquants = []
if not doc1: manquants.append("Questionnaire TRC")
if not doc2: manquants.append("CCTP")
if not doc3: manquants.append("Descriptif technique")
if not doc4: manquants.append("Étude de sol")
if not doc5: manquants.append("Planning")
if type_travaux == "Route" and not doc6: manquants.append("Ouvrages d'art")

if manquants:
    st.warning("Veuillez joindre les documents qui vous ont aidé à l'appréciation du risque : " + ", ".join(manquants))
else:
    st.success("✅ **Tous les documents requis ont été joints.**")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. Extensions de garantie
# ---------------------------------------------------------
st.markdown('<div class="section-title">Extensions de garantie</div>', unsafe_allow_html=True)

# NOUVEAU: Suppléments RC
st.markdown('<div class="section-subtitle">Garantie Responsabilité Civile (RC)</div>', unsafe_allow_html=True)
ext_rc = st.checkbox("Inclure la Responsabilité Civile (A17)", value=True)

rc1, rc2 = st.columns(2)
rc_suppl_trafic_key = rc1.selectbox(
    "Supp. RC : Rues et places publiques adjacentes",
    list(RC_SUPPLEMENTS["trafic"].keys()),
    disabled=not ext_rc
)
rc_suppl_prox_key = rc2.selectbox(
    "Supp. RC : Immeubles ou ouvrages de proximité",
    list(RC_SUPPLEMENTS["proximite"].keys()),
    disabled=not ext_rc
)
ext_rc_croisee = st.checkbox("Inclure RC croisée (surprime +20% sur la prime RC)", disabled=not ext_rc)

# Autres extensions
st.markdown('<div class="section-subtitle">Autres garanties (sur taux travaux)</div>', unsafe_allow_html=True)
e1, e2, e3 = st.columns(3)
ext_deblais = e1.checkbox("Frais de déblais (+0,15‰)", help="Ajoute 0,15‰ au taux travaux. Limité à 5% du montant sinistre.")
ext_maintenance = e2.checkbox("Maintenance visite (A05)", help="Prime additionnelle = 10% de la prime travaux de base.")
ext_existants = e3.checkbox("Dommages aux existants (A20)", help="Couvre les biens existants jusqu'à 20% du montant des travaux, avec un taux de 50% du taux net travaux.")

# NOUVEAU: Extensions soumises à DT
# MODIFICATION: Organisation en grille 3x2
st.markdown('<div class="section-subtitle">Garanties additionnelles (soumises à la Direction Technique)</div>', unsafe_allow_html=True)
dt1, dt2, dt3 = st.columns(3)
ext_gemp = dt1.checkbox("Grèves, Émeutes, Mvts Pop. (FANAF 01)")
ext_maint_etendue = dt2.checkbox("Maintenance étendue (A06)")
ext_maint_const = dt3.checkbox("Maintenance constructeur (A07)")

# Deuxième ligne pour l'alignement
dt4, dt5, dt6 = st.columns(3)
ext_materiel = dt4.checkbox("Matériel et engins de chantier (A21)")
ext_baraquement = dt5.checkbox("Baraquements et Entrepôts (A22)")

extensions_dt = []
if ext_gemp: extensions_dt.append("Grèves/Émeutes (FANAF 01)")
if ext_maint_etendue: extensions_dt.append("Maintenance étendue (A06)")
if ext_maint_const: extensions_dt.append("Maintenance constructeur (A07)")
if ext_materiel: extensions_dt.append("Matériel (A21)")
if ext_baraquement: extensions_dt.append("Baraquements (A22)")

if extensions_dt:
    st.info("ℹ️ **Les extensions suivantes nécessitent une tarification manuelle de la Direction Technique :** " + ", ".join(extensions_dt))

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5bis. ÉQUIPEMENTS ET INSTALLATIONS DE CHANTIER (A21, A22)
# ---------------------------------------------------------
# Cette section n'apparaît que si les clauses A21 ou A22 sont cochées
if ext_materiel or ext_baraquement:
    st.markdown('<div class="section-title">Équipements et Installations de Chantier</div>', unsafe_allow_html=True)
    st.info("ℹ️ Cette section permet de tarifer les équipements et installations de chantier (A21, A22). Chaque équipement est tarifé individuellement selon sa classe de risque, sa durée et sa franchise.")
    
    # Classification du chantier
    st.markdown('<div class="section-subtitle">Classification du chantier</div>', unsafe_allow_html=True)
    st.markdown("**Classe de risque du chantier**")
    st.markdown("""
    - **Classe 1** : Chantiers situés en zones isolées non inondables, terrains plats ou à faibles déclivités ; pas d'excavation profonde, pas de tranchée importante.
    - **Classe 2** : Chantiers situés en zones soumises à possibilités d'inondations ; excavations profondes, tranchées ; terrains difficiles (déclivités, risques de glissements).
    - **Classe 3** : Chantiers en zones très exposées ; possibilité d'inondations, tempête ou tremblement de terre ; travaux en montagne, fortes déclivités, risques de chutes de roches, glissement de terrains, etc.
    """)
    
    classe_chantier = st.selectbox(
        "Sélectionnez la classe",
        ["Classe 1", "Classe 2", "Classe 3"],
        label_visibility="collapsed"
    )
    
    # Initialisation de la liste des équipements dans session_state
    if 'equipements' not in st.session_state:
        st.session_state.equipements = []
    
    st.markdown('<div class="section-subtitle">Liste des équipements à assurer</div>', unsafe_allow_html=True)
    
    # Formulaire d'ajout d'équipement
    with st.expander("➕ Ajouter un équipement", expanded=len(st.session_state.equipements) == 0):
        type_eq = st.selectbox(
            "Type d'équipement",
            ["--- Grues ---", "Grue à tour", "Grue automobile", 
             "--- Engins mobiles ---", "Bulldozers, niveleuses, scrapers", "Chargeurs, dumpers", 
             "Compacteurs vibrants", "Sonnettes / extracteurs de pieux", "Rouleaux compresseurs", 
             "Locomotives de chantier",
             "--- Baraquements ---", "Baraquement de stockage", "Bureaux provisoires de chantier"],
            key="type_eq_add"
        )
        
        # Ne pas permettre de sélectionner les séparateurs
        if type_eq.startswith("---"):
            st.warning("Veuillez sélectionner un type d'équipement valide")
            type_eq_valide = False
        else:
            type_eq_valide = True
            
        col_eq1, col_eq2 = st.columns(2)
        designation = col_eq1.text_input("Désignation / Description", key="design_add")
        valeur_eq = col_eq2.number_input("Valeur à neuf (FCFA)", min_value=0, value=0, step=100_000, format="%d", key="valeur_add")
        
        col_eq3, col_eq4 = st.columns(2)
        duree_eq = col_eq3.number_input("Durée de présence (mois)", min_value=1, max_value=36, value=12, key="duree_add")
        franchise_eq = col_eq4.selectbox(
            "Franchise",
            list(RABAIS_FRANCHISE_EQUIPEMENTS.keys()),
            key="franchise_add"
        )
        
        if st.button("Ajouter cet équipement", type="primary", disabled=not type_eq_valide or not designation or valeur_eq == 0):
            st.session_state.equipements.append({
                "type": type_eq,
                "designation": designation,
                "valeur": valeur_eq,
                "duree": duree_eq,
                "franchise": franchise_eq,
                "classe": classe_chantier
            })
            st.success(f"✅ {designation} ajouté(e) !")
            st.rerun()
    
    # Affichage de la liste des équipements
    if st.session_state.equipements:
        st.markdown("**Équipements ajoutés :**")
        for idx, eq in enumerate(st.session_state.equipements):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{idx+1}. {eq['designation']}** ({eq['type']})")
                st.caption(f"Valeur: {eq['valeur']:,.0f} FCFA | Durée: {eq['duree']} mois | Franchise: {eq['franchise']}")
            
            with col2:
                # Calcul de la prime pour cet équipement
                if eq['type'] == "Grue à tour":
                    taux = get_taux_grue_tour(eq['valeur'], eq['classe'])
                elif eq['type'] in TARIFS_BARAQUEMENTS:
                    taux = get_taux_baraquement(eq['type'])
                else:
                    taux = get_taux_engin(eq['type'], eq['classe'])
                
                coef_franchise = RABAIS_FRANCHISE_EQUIPEMENTS[eq['franchise']]
                prime_eq = calc_prime_equipement(eq['valeur'], taux, eq['duree'], coef_franchise)
                st.metric("Prime", f"{prime_eq:,.0f} FCFA")
            
            with col3:
                if st.button("🗑️", key=f"del_{idx}", help="Supprimer"):
                    st.session_state.equipements.pop(idx)
                    st.rerun()
        
        # Total des primes équipements
        prime_totale_equipements = sum([
            calc_prime_equipement(
                eq['valeur'],
                get_taux_grue_tour(eq['valeur'], eq['classe']) if eq['type'] == "Grue à tour"
                else (get_taux_baraquement(eq['type']) if eq['type'] in TARIFS_BARAQUEMENTS
                      else get_taux_engin(eq['type'], eq['classe'])),
                eq['duree'],
                RABAIS_FRANCHISE_EQUIPEMENTS[eq['franchise']]
            )
            for eq in st.session_state.equipements
        ])
        
        st.markdown("---")
        st.metric("**Prime totale Équipements et Installations**", f"**{prime_totale_equipements:,.0f} FCFA**")
    else:
        st.info("Aucun équipement ajouté. Utilisez le formulaire ci-dessus pour en ajouter.")
else:
    # Si les extensions A21/A22 ne sont pas cochées, réinitialiser la liste
    if 'equipements' in st.session_state:
        st.session_state.equipements = []
    prime_totale_equipements = 0

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. Saisie manuelle (si montant > 2 milliards OU validation DT OU volontaire)
# ---------------------------------------------------------
if mode_manuel:
    st.markdown('<div class="section-title">Tarification manuelle</div>', unsafe_allow_html=True)
    
    # Déterminer le message approprié selon le contexte
    if raison_manuel == "montant_eleve":
        st.info("ℹ️ **Le montant dépasse 2 milliards FCFA.** Veuillez saisir la Prime Nette et les Accessoires fournis par la Direction Technique. Les taxes et la prime TTC seront calculés automatiquement.")
    elif raison_manuel == "validation_dt":
        st.info("ℹ️ **Tarification manuelle de la Direction Technique.** Veuillez saisir la Prime Nette et les Accessoires fournis. Les taxes et la prime TTC seront calculés automatiquement.")
    elif raison_manuel == "volontaire":
        st.info("ℹ️ **Tarification manuelle (hors barème).** Veuillez saisir la Prime Nette et les Accessoires. Les taxes et la prime TTC seront calculés automatiquement.")
    
    col_m1, col_m2 = st.columns(2)
    prime_nette_manuelle = col_m1.number_input("Prime Nette (FCFA)", min_value=0, value=0, step=10_000, format="%d", key="prime_nette_man")
    accessoires_manuels = col_m2.number_input("Accessoires (FCFA)", min_value=0, value=0, step=1_000, format="%d", key="accessoires_man")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. Bouton de calcul
# ---------------------------------------------------------
# Désactiver le bouton si: (1) il y a des alertes ET (2) on n'est pas en mode manuel
desactiver_calcul = (len(alerts) > 0) and not mode_manuel
calcule = st.button("Calculer la prime", type="primary", use_container_width=True, disabled=desactiver_calcul)

# ---------------------------------------------------------
# 9. Calculs & Affichage des résultats
# ---------------------------------------------------------
if calcule:
    if mode_manuel:
        # MODE MANUEL : Utiliser les valeurs saisies
        prime_nette = prime_nette_manuelle
        accessoires = accessoires_manuels
        taxes = calc_taxes(prime_nette, accessoires)
        prime_ttc = prime_nette + accessoires + taxes
        
        # Pas de décomposition détaillée en mode manuel
        taux_net_travaux = 0
        prime_travaux = 0
        prime_maintenance = 0
        prime_rc = 0
        prime_existants = 0
        taux_rc_final = 0
        
    else:
        # MODE AUTOMATIQUE : Calcul normal
        # 1. Taux de base travaux (‰)
        taux_base = get_taux_base(type_travaux, duree, usage_key, structure)
        
        # 2. Ajustement franchise
        taux_base_franchise = taux_base * FRANCHISE_COEF[franchise_key]
        
        # 3. Taux net travaux (avec extensions sur taux)
        taux_net_travaux = taux_base_franchise
        if ext_deblais:
            taux_net_travaux += 0.15 # Ajout 0,15‰
        
        # 4. Calcul Prime TRAVAUX
        prime_travaux = calc_prime(montant, taux_net_travaux)
        
        # 5. Calcul Prime MAINTENANCE (A05)
        prime_maintenance = 0
        if ext_maintenance:
            # (MODIFIÉ) Prime = 10% de la prime travaux (calculée sur le taux de base + franchise)
            prime_maintenance_base = calc_prime(montant, taux_base_franchise)
            prime_maintenance = prime_maintenance_base * 0.10
            
        # 6. Calcul Prime RC (A17)
        prime_rc = 0
        taux_rc_final = 0
        if ext_rc:
            # Taux RC calculé sur Taux Net Travaux (incluant déblais)
            taux_rc_final = calc_taux_rc(
                type_travaux, 
                taux_net_travaux, 
                rc_suppl_trafic_key, 
                rc_suppl_prox_key, 
                ext_rc_croisee
            )
            prime_rc = calc_prime(montant, taux_rc_final)
            
        # 7. Calcul Prime DOMMAGES AUX EXISTANTS (A20)
        prime_existants = 0
        if ext_existants:
            # Plafond de garantie = 20% du montant travaux
            valeur_existants = 0.2 * montant
            # Taux = 50% du Taux Net Travaux (Taux base + extensions hors GEMP)
            taux_existants = taux_net_travaux * 0.5
            prime_existants = calc_prime(valeur_existants, taux_existants)

        # 8. Primes totales (incluant équipements si applicable)
        prime_nette = prime_travaux + prime_maintenance + prime_rc + prime_existants + prime_totale_equipements
        accessoires = calc_accessoires(prime_nette)
        taxes = calc_taxes(prime_nette, accessoires)
        prime_ttc = prime_nette + accessoires + taxes

    # ---------------------------------------------------------
    # Affichage des résultats
    # ---------------------------------------------------------
    st.markdown('<div class="section-title">Résultats de la cotation</div>', unsafe_allow_html=True)
    
    if mode_manuel:
        # Affichage simplifié pour le mode manuel avec message contextualisé
        if raison_manuel == "montant_eleve":
            st.info("ℹ️ **Tarification manuelle** (montant > 2 milliards FCFA)")
        elif raison_manuel == "validation_dt":
            st.info("ℹ️ **Tarification manuelle** (validation Direction Technique)")
        elif raison_manuel == "volontaire":
            st.info("ℹ️ **Tarification manuelle** (hors barème - choix volontaire)")
    else:
        # Tableau de décomposition (mode automatique uniquement)
        st.markdown("**Décomposition de la prime**")
        
        # Création d'un tableau simple
        decomposition_data = []
        
        # Prime Travaux
        decomposition_data.append({
            "Garantie": "Prime Travaux",
            "Montant (FCFA)": f"{prime_travaux:,.0f}",
            "Taux (‰)": f"{taux_net_travaux:.3f}"
        })
        
        # Prime Maintenance (si applicable)
        if ext_maintenance:
            decomposition_data.append({
                "Garantie": "Prime Maintenance Visite (A05)",
                "Montant (FCFA)": f"{prime_maintenance:,.0f}",
                "Taux (‰)": "-"
            })
        
        # Prime RC (si applicable)
        if ext_rc:
            decomposition_data.append({
                "Garantie": "Prime Responsabilité Civile (A17)",
                "Montant (FCFA)": f"{prime_rc:,.0f}",
                "Taux (‰)": f"{taux_rc_final:.3f}"
            })
        
        # Prime Existants (si applicable)
        if ext_existants:
            decomposition_data.append({
                "Garantie": "Prime Dommages aux Existants (A20)",
                "Montant (FCFA)": f"{prime_existants:,.0f}",
                "Taux (‰)": f"{taux_net_travaux * 0.5:.3f}"
            })
        
        # Prime Équipements (si applicable)
        if prime_totale_equipements > 0:
            decomposition_data.append({
                "Garantie": f"Prime Équipements et Installations (A21/A22) - {len(st.session_state.equipements)} équipement(s)",
                "Montant (FCFA)": f"{prime_totale_equipements:,.0f}",
                "Taux (‰)": "-"
            })
        
        # Affichage du tableau
        import pandas as pd
        df_decomposition = pd.DataFrame(decomposition_data)
        st.dataframe(df_decomposition, use_container_width=True, hide_index=True)
    
    # Total
    st.markdown("**Total**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prime Nette", f"{prime_nette:,.0f} FCFA")
    col2.metric("Accessoires", f"{accessoires:,.0f} FCFA")
    col3.metric("Taxes (14.5%)", f"{taxes:,.0f} FCFA")
    col4.metric("**PRIME TTC**", f"**{prime_ttc:,.0f} FCFA**")


    # NOUVEAU: Affichage des clauses
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Clauses à insérer au contrat</div>', unsafe_allow_html=True)
    
    st.markdown("<h6>Clauses Obligatoires</h6>", unsafe_allow_html=True)
    for clause in CLAUSES["obligatoires"][type_travaux]:
        st.write(f"- {clause}")
        
    st.markdown("<h6>Clauses relatives aux extensions souscrites</h6>", unsafe_allow_html=True)
    clauses_ext_actives = []
    if ext_maintenance: clauses_ext_actives.append(CLAUSES["extensions"]["A05"])
    if ext_rc: clauses_ext_actives.append(CLAUSES["extensions"]["A17"]) # A17 est la RC
    if ext_rc_croisee: clauses_ext_actives.append("A17 (RC Croisée)") # Précision
    if ext_existants: clauses_ext_actives.append(CLAUSES["extensions"]["A20"])
    # Celles soumises à DT
    if ext_maint_etendue: clauses_ext_actives.append(CLAUSES["extensions"]["A06"])
    if ext_maint_const: clauses_ext_actives.append(CLAUSES["extensions"]["A07"])
    if ext_materiel: clauses_ext_actives.append(CLAUSES["extensions"]["A21"])
    if ext_baraquement: clauses_ext_actives.append(CLAUSES["extensions"]["A22"])
    if ext_gemp: clauses_ext_actives.append(CLAUSES["extensions"]["FANAF01"])
    
    if clauses_ext_actives:
        for clause in clauses_ext_actives:
            st.write(f"- {clause}")
    else:
        st.info("Aucune extension (A05, A06, A07, A17, A20, A21, A22, FANAF01) n'a été sélectionnée.")
