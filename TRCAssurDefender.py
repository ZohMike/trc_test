import streamlit as st
import base64
from fpdf import FPDF
import datetime
import pandas as pd

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

# Options pour la structure (pour le selectbox)
STRUCTURE_OPTIONS = {
    "Type A (Béton armé/acier, portée < 10m)": "A",
    "Type B (Acier/précontraint, portée 10-15m)": "B",
}

# Coefficients de franchise basés sur les images
FRANCHISE_COEF = {
    "Normale (x1)": 1.0,
    "Multipliée par 2 (Rabais 7,5%)": 0.925,
    "Multipliée par 5 (Rabais 15%)": 0.85,
    "Multipliée par 10 (Rabais 25%)": 0.75,
    "Divisée par 2 (Augmentation 25%)": 1.25,
}

# Paramètres RC (Taux / Minimum)
RC_PARAMS = {
    "Bâtiment": {"pct": 0.15, "min": 0.35},
    "Assainissement": {"pct": 0.20, "min": 0.40},
    "Route": {"pct": 0.20, "min": 0.40},
}

# Suppléments RC (basés sur les images)
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

# Dictionnaire des clauses
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
        "A20": "Dommages aux Existants (clause A20)",
        "A21": "Matériel et installations de chantier (clause A21)",
        "A22": "Baraquements provisoires (clause A22)",
        "FANAF01": "Garantie Environnement, Modification Paysagère (clause FANAF01)",
    },
}

# =========================================================
# EXCLUSIONS PAR DÉFAUT (Nouveau champ)
# =========================================================
EXCLUSIONS_DEFAUT = """- Erosion naturelle
- Coffrage, cintres et echafaudages
- Tassement de terrain en dehors des tassements accidentels
- Dommage cause par les vibrations, la suppression des points d'appuis
- Frais d'assechement et d'injection
- Mauvais beton,
- Greve, Emeute, Mouvement populaire
- Dommages aux Recoltes Forets Cultures
- RC Professionnelle,
- Faute intentionnelle des preposes de l'assure
- Reserves du bureau de controle
- Travaux de demolition et travaux sur les structures et murs porteurs"""

# =========================================================
# FONCTIONS
# =========================================================

def get_taux_base(type_travaux, duree, usage_key, structure):
    """Retourne le taux de base (‰) en fonction du type de travaux"""
    duree_key = "18m" if duree > 12 else "12m"
    
    if type_travaux == "Bâtiment":
        return TARIFS_BATIMENT[usage_key][structure][duree_key]
    elif type_travaux == "Assainissement":
        return TARIF_ASSAINISSEMENT[duree_key]
    elif type_travaux == "Route":
        return TARIF_ROUTES[duree_key]
    else:
        return 0.0

def calc_prime(montant, taux):
    """Calcule la prime à partir du montant (FCFA) et du taux (‰)"""
    return montant * (taux / 1000)

def calc_taux_rc(type_travaux, taux_travaux, trafic_key, prox_key, rc_croisee):
    """Calcule le taux RC final (‰)"""
    params = RC_PARAMS[type_travaux]
    taux_base_rc = max(taux_travaux * params["pct"], params["min"])
    
    coef_trafic = RC_SUPPLEMENTS["trafic"][trafic_key]
    coef_prox = RC_SUPPLEMENTS["proximite"][prox_key]
    taux_rc = taux_base_rc * coef_trafic * coef_prox
    
    if rc_croisee:
        taux_rc *= 1.10
    
    return taux_rc

def calc_accessoires(prime_nette):
    """Calcule les accessoires (6% de la prime nette)"""
    return prime_nette * 0.06

def calc_taxes(prime_nette, accessoires):
    """Calcule les taxes (14.5% de (prime nette + accessoires))"""
    return (prime_nette + accessoires) * 0.145

def generate_pdf(data):
    """
    Génère un PDF de proposition de cotation TRC selon le modèle Leadway Assurance
    """
    from fpdf import FPDF
    import datetime
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def table_row_multicell(pdf, widths, texts, height=5, align=['L','C','C','C'], border=1, fill=False, font_style=''):
        """
        Crée une ligne de tableau avec support multi-lignes pour chaque cellule.
        widths: liste des largeurs de colonnes
        texts: liste des textes pour chaque colonne
        height: hauteur de ligne minimale
        align: alignement pour chaque colonne
        border: style de bordure (0=aucune, 1=bordure)
        fill: remplissage de fond
        font_style: style de police ('B' pour gras, '' pour normal)
        """
        # Sauvegarder la position de départ
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        
        # Sauvegarder le style de police actuel
        current_font = pdf.font_family
        current_size = pdf.font_size_pt
        current_style = pdf.font_style
        
        # Appliquer le style si spécifié
        if font_style:
            pdf.set_font(current_font, font_style, current_size)
        
        # Calculer la hauteur maximale nécessaire pour chaque cellule
        max_height = height
        for i, (width, text) in enumerate(zip(widths, texts)):
            if text:
                # Utiliser multi_cell en mode split_only pour calculer le nombre de lignes
                temp_y = pdf.get_y()
                temp_x = pdf.get_x()
                pdf.set_xy(start_x, start_y)
                
                # Calculer combien de lignes nécessaires
                lines = pdf.multi_cell(width, height, text, border=0, align=align[i], split_only=True)
                num_lines = len(lines) if lines else 1
                cell_height = num_lines * height
                
                if cell_height > max_height:
                    max_height = cell_height
                
                pdf.set_xy(temp_x, temp_y)
        
        # Dessiner les bordures de la ligne complète
        if border:
            pdf.rect(start_x, start_y, sum(widths), max_height)
            # Dessiner les séparateurs verticaux
            x_pos = start_x
            for width in widths[:-1]:
                x_pos += width
                pdf.line(x_pos, start_y, x_pos, start_y + max_height)
        
        # Remplir chaque cellule avec le texte
        x_pos = start_x
        for i, (width, text, alignment) in enumerate(zip(widths, texts, align)):
            pdf.set_xy(x_pos, start_y)
            
            # Dessiner le texte sans bordure (déjà dessinée)
            if text:
                # Calculer le nombre de lignes pour ce texte
                lines = pdf.multi_cell(width, height, '', border=0, align=alignment, split_only=True)
                num_lines = len(pdf.multi_cell(width, height, text, border=0, align=alignment, split_only=True)) if text else 1
                text_height = num_lines * height
                
                # Centrer verticalement si le texte est plus court que max_height
                y_offset = (max_height - text_height) / 2 if text_height < max_height else 0
                pdf.set_xy(x_pos, start_y + y_offset)
            
            # Écrire le texte
            pdf.multi_cell(width, height, text, border=0, align=alignment, fill=fill)
            
            x_pos += width
        
        # Restaurer le style de police original
        pdf.set_font(current_font, current_style, current_size)
        
        # Se positionner après la ligne
        pdf.set_xy(start_x, start_y + max_height)
    
    # Utiliser DejaVu pour supporter UTF-8
    try:
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
        font_name = "DejaVu"
    except:
        font_name = "Arial"
    
    def clean_text(text):
        if font_name == "Arial":
            replacements = {
                'œ': 'oe', 'Œ': 'OE', 'à': 'a', 'â': 'a', 'ä': 'a',
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'î': 'i', 'ï': 'i', 'ô': 'o', 'ö': 'o',
                'ù': 'u', 'û': 'u', 'ü': 'u', 'ç': 'c',
                'À': 'A', 'Â': 'A', 'Ä': 'A',
                'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
                'Î': 'I', 'Ï': 'I', 'Ô': 'O', 'Ö': 'O',
                'Ù': 'U', 'Û': 'U', 'Ü': 'U', 'Ç': 'C'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
        return text
    
    def format_amount_fr(amount):
        """Formats a number with space as a thousand separator and no decimal part."""
        # Use locale-independent formatting, then replace comma with space
        # Assumes f-string formatting uses comma for thousands in the environment
        return f"{amount:,.0f}".replace(",", " ")

    
    # ============================================================
    # PAGE 1 - EN-TÊTE ET INFORMATIONS GÉNÉRALES
    # ============================================================
    
    # Logo et date
    pdf.set_font(font_name, "B", 12)
    pdf.cell(100, 10, clean_text("LEADWAY"), 0, 0, 'L')
    today = datetime.date.today()
    pdf.cell(0, 10, clean_text(f"Abidjan, le {today.strftime('%d.%m.%Y')}"), 0, 1, 'R')
    pdf.set_font(font_name, "", 10)
    pdf.cell(100, 5, clean_text("Assurance"), 0, 1, 'L')
    pdf.ln(5)
    
    # BANDEAU JAUNE - TITRE PRINCIPAL
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font(font_name, "B", 16)
    pdf.cell(0, 10, clean_text("OFFRE D'ASSURANCE"), 0, 1, 'C', fill=True)
    pdf.set_font(font_name, "B", 14)
    pdf.cell(0, 8, clean_text("TOUS RISQUES CHANTIER"), 0, 1, 'C', fill=True)
    pdf.set_font(font_name, "B", 12)
    prospect_text = f"Prospect : {data.get('souscripteur', 'N/A').upper()}"
    pdf.cell(0, 8, clean_text(prospect_text), 0, 1, 'C', fill=True)
    
    pdf.ln(5)
    pdf.set_font(font_name, "", 9)
    intro_text = f"Comme suite a votre demande de cotation du {data.get('date_demande', today.strftime('%d/%m/%Y'))} nous vous presentons ci-dessous les conditions de garanties et de primes pour la couverture TRC sollicitee."
    pdf.multi_cell(0, 5, clean_text(intro_text), 0, 'L')
    
    pdf.ln(5)
    
    # SECTION 1 : CARACTÉRISTIQUES DU RISQUE
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("1.    CARACTERISTIQUES DU RISQUE"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 9)
    
    # Informations en tableau 2 colonnes
    caracteristiques_data = [
        ("Nom ou raison sociale", data.get('souscripteur', ''), 
         "Duree des travaux", f"{data.get('duree', '')} mois (Date de debut a preciser)"),
        ("Situation du chantier", data.get('situation_geo', ''), 
         "Maitre d'ouvrage", data.get('maitre_ouvrage', '')),
        ("Nature du chantier", data.get('nature_travaux', ''), 
         "Maitre d'oeuvre", data.get('maitrise_oeuvre', '')),
        ("", "", 
         "Controle Technique", data.get('bureau_controle', 'A nous communiquer')),
        ("Montant des travaux", f"{format_amount_fr(data.get('montant', 0))} F CFA", 
         "Duree de Maintenance", f"{data.get('duree_maintenance', '12')} mois"),
    ]
    
    for left_label, left_value, right_label, right_value in caracteristiques_data:
        # Colonne gauche
        if left_label:
            pdf.set_font(font_name, "B", 9)
            pdf.cell(45, 6, clean_text(left_label), 0, 0, 'L')
            pdf.set_font(font_name, "", 9)
            pdf.cell(50, 6, clean_text(f": {left_value}"), 0, 0, 'L')
        else:
            pdf.cell(95, 6, "", 0, 0, 'L')
        
        # Colonne droite
        if right_label:
            pdf.set_font(font_name, "B", 9)
            pdf.cell(40, 6, clean_text(right_label), 0, 0, 'L')
            pdf.set_font(font_name, "", 9)
            pdf.cell(0, 6, clean_text(f": {right_value}"), 0, 1, 'L')
        else:
            pdf.ln()
    
    pdf.ln(5)
    
    # SECTION 2 : GARANTIES ACCORDEES
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("2.    GARANTIES ACCORDEES"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 9)
    pdf.cell(10, 6, clean_text("-"), 0, 0, 'L')
    pdf.cell(0, 6, clean_text("Dommages directs a l'ouvrage"), 0, 1, 'L')
    pdf.cell(10, 6, clean_text("-"), 0, 0, 'L')
    pdf.cell(0, 6, clean_text("RC+ RC Croisee"), 0, 1, 'L')
    
    pdf.ln(5)
    
    # ============================================================
    # SECTION 3 : PRIMES (Anciennement Section 4)
    # ============================================================
    
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("3.    PRIMES"), 0, 1, 'L')
    pdf.ln(2)
    
    # Tableau des primes
    pdf.set_font(font_name, "", 9)
    
    primes_data = [
        ("Prime nette previsionnelle Initiale", format_amount_fr(data.get('prime_nette', 0)), "F CFA"),
        ("Reduction commerciale", format_amount_fr(data.get('reduction_commerciale', 0)), "F CFA"),
        ("Prime nette previsionnelle finale", format_amount_fr(data.get('prime_nette_finale', data.get('prime_nette', 0))), "F CFA"),
        ("Accessoires", format_amount_fr(data.get('accessoires', 0)), "F CFA"),
        ("Taxes", format_amount_fr(data.get('taxes', 0)), "F CFA"),
    ]
    
    for label, value, devise in primes_data:
        pdf.set_font(font_name, "B", 9)
        pdf.cell(80, 6, clean_text(label), 0, 0, 'L')
        pdf.set_font(font_name, "", 9)
        pdf.cell(10, 6, ":", 0, 0, 'C')
        pdf.cell(50, 6, clean_text(value), 0, 0, 'R')
        pdf.cell(0, 6, clean_text(devise), 0, 1, 'L')
    
    # Prime TTC
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font(font_name, "B", 10)
    pdf.cell(80, 7, clean_text("Prime TTC"), 0, 0, 'L', fill=True)
    pdf.cell(10, 7, ":", 0, 0, 'C', fill=True)
    pdf.cell(50, 7, format_amount_fr(data.get('prime_ttc', 0)), 0, 0, 'R', fill=True)
    pdf.cell(0, 7, clean_text("F CFA"), 0, 1, 'L', fill=True)
    
    pdf.ln(10)
    
    # ============================================================
    # SECTION 4 : LIMITES DE GARANTIES ET FRANCHISES (Anciennement Section 3)
    # ============================================================
    
    pdf.add_page() # Ajout d'un saut de page
    
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("4.    LIMITES DE GARANTIES ET FRANCHISES"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 9)
    territoire_text = "Les garanties s'exercent exclusivement sur le territoire ivoirien."
    pdf.multi_cell(0, 5, clean_text(territoire_text), 0, 'L')
    
    pdf.ln(3)
    
    # TABLEAU DES GARANTIES
    
    # En-tête du tableau
    pdf.set_fill_color(255, 204, 0)  # Jaune
    pdf.set_font(font_name, "B", 9)
    
    # Ajustement des largeurs de colonnes
    col1_w = 95  # Désignation des garanties (inchangé)
    col2_w = 25  # Statut (Réduit de 30 à 25)
    col3_w = 30  # Capitaux (Réduit de 35 à 30)
    col4_w = 40  # Franchises (Augmenté de 30 à 40)
    
    pdf.cell(col1_w, 6, clean_text("DESIGNATION DES GARANTIES"), 1, 0, 'C', fill=True)
    pdf.cell(col2_w, 6, clean_text("STATUT"), 1, 0, 'C', fill=True)
    pdf.cell(col3_w, 6, clean_text("CAPITAUX"), 1, 0, 'C', fill=True)
    pdf.cell(col4_w, 6, clean_text("FRANCHISES"), 1, 1, 'C', fill=True)
    
    # I- DOMMAGES DIRECTS A L'OUVRAGE
    pdf.set_fill_color(200, 200, 200)  # Gris clair
    pdf.set_font(font_name, "B", 9)
    pdf.cell(col1_w + col2_w + col3_w + col4_w, 6, clean_text("I-        DOMMAGES DIRECTS A L'OUVRAGE"), 1, 1, 'L', fill=True)
    
    pdf.set_font(font_name, "", 7)
    
    # Période des travaux (Ligne 1)
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Periode des travaux"), 
                        clean_text("Garanti"), 
                        format_amount_fr(data.get('montant', 0)), 
                        clean_text("Evnts. Naturels et maintenance")],
                       height=5,
                       align=['L', 'C', 'R', 'C'],
                       font_style='B')
    
    # Période de maintenance (Ligne 2)
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Periode de maintenance"), 
                        clean_text("Garanti"), 
                        format_amount_fr(data.get('montant', 0)), 
                        clean_text("10% mini 15 000 000")],
                       height=5,
                       align=['L', 'C', 'R', 'C'],
                       font_style='B')
    
    # Extension de garanties (ligne titre)
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Extension de garanties"), "", "", ""],
                       height=5,
                       align=['L', 'C', 'C', 'C'],
                       font_style='B')
    
    # Liste complète des extensions selon l'image - DYNAMIQUE
    
    # Honoraires d'expert
    honoraires_statut = "Garanti" if data.get('ext_honoraires_expert') else "Exclu"
    honoraires_cap = data.get('honoraires_capitaux', '') if data.get('ext_honoraires_expert') else ''
    honoraires_fran = data.get('honoraires_franchises', '') if data.get('ext_honoraires_expert') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Honoraires d'expert"), 
                        clean_text(honoraires_statut), 
                        clean_text(honoraires_cap if honoraires_cap else 'Selon bareme des experts'), 
                        clean_text(honoraires_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Dommages aux biens et existants
    existants_statut = "Garanti" if data.get('ext_existants') else "Exclu"
    existants_cap = data.get('existants_capitaux', '') if data.get('ext_existants') else ''
    existants_fran = data.get('existants_franchises', '') if data.get('ext_existants') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Dommages aux biens et existants"), 
                        clean_text(existants_statut), 
                        clean_text(existants_cap), 
                        clean_text(existants_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Erreur de conception
    erreur_statut = "Garanti" if data.get('ext_erreur_conception') else "Exclu"
    erreur_cap = data.get('erreur_capitaux', '') if data.get('ext_erreur_conception') else ''
    erreur_fran = data.get('erreur_franchises', '') if data.get('ext_erreur_conception') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Erreur de conception (Y compris parties viciees)"), 
                        clean_text(erreur_statut), 
                        clean_text(erreur_cap), 
                        clean_text(erreur_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Engins de chantier
    engins_statut = "Garanti" if (data.get('ext_materiel') or data.get('ext_baraquement')) else "Exclu"
    engins_cap = data.get('materiel_capitaux', '') if data.get('ext_materiel') else ''
    engins_fran = data.get('materiel_franchises', '') if data.get('ext_materiel') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Engins de chantier"), 
                        clean_text(engins_statut), 
                        clean_text(engins_cap), 
                        clean_text(engins_fran)],
                       height=5,
                       align=['L', 'C', 'C', 'C'])
    
    # Heures supplémentaires
    heures_statut = "Garanti" if data.get('ext_heures_suppl') else "Exclu"
    heures_cap = data.get('heures_capitaux', '') if data.get('ext_heures_suppl') else ''
    heures_fran = data.get('heures_franchises', '') if data.get('ext_heures_suppl') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Heures supplementaires, Travail de nuit, Transport a grande vitesse"), 
                        clean_text(heures_statut), 
                        clean_text(heures_cap), 
                        clean_text(heures_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Vol des biens entreposés
    vol_statut = "Garanti" if data.get('ext_vol_entrepose') else "Exclu"
    vol_cap = data.get('vol_entrepose_capitaux', '') if data.get('ext_vol_entrepose') else ''
    vol_fran = data.get('vol_entrepose_franchises', '') if data.get('ext_vol_entrepose') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Vol des biens entreposes hors chantier"), 
                        clean_text(vol_statut), 
                        clean_text(vol_cap), 
                        clean_text(vol_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Transport terrestre
    trans_terr_statut = "Garanti" if data.get('ext_transport_terrestre') else "Exclu"
    trans_terr_cap = data.get('transport_terrestre_capitaux', '') if data.get('ext_transport_terrestre') else ''
    trans_terr_fran = data.get('transport_terrestre_franchises', '') if data.get('ext_transport_terrestre') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Transport terrestre"), 
                        clean_text(trans_terr_statut), 
                        clean_text(trans_terr_cap), 
                        clean_text(trans_terr_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Transport aérien
    trans_aer_statut = "Garanti" if data.get('ext_transport_aerien') else "Exclu"
    trans_aer_cap = data.get('transport_aerien_capitaux', '') if data.get('ext_transport_aerien') else ''
    trans_aer_fran = data.get('transport_aerien_franchises', '') if data.get('ext_transport_aerien') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Transport aerien"), 
                        clean_text(trans_aer_statut), 
                        clean_text(trans_aer_cap), 
                        clean_text(trans_aer_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Baraquement
    baraq_statut = "Garanti" if data.get('ext_baraquement') else "Exclu"
    baraq_cap = data.get('baraquement_capitaux', '') if data.get('ext_baraquement') else ''
    baraq_fran = data.get('baraquement_franchises', '') if data.get('ext_baraquement') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Baraquement, entrepot, bureaux provisoires"), 
                        clean_text(baraq_statut), 
                        clean_text(baraq_cap), 
                        clean_text(baraq_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Conduits et Souterrains
    conduits_statut = "Garanti" if data.get('ext_conduits_souterrains') else "Exclu"
    conduits_cap = data.get('conduits_capitaux', '') if data.get('ext_conduits_souterrains') else ''
    conduits_fran = data.get('conduits_franchises', '') if data.get('ext_conduits_souterrains') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Conduits et Souterrains"), 
                        clean_text(conduits_statut), 
                        clean_text(conduits_cap), 
                        clean_text(conduits_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Tempête, GEMP
    gemp_statut = "Garanti" if data.get('ext_gemp') else "Exclu"
    gemp_cap = data.get('gemp_capitaux', '') if data.get('ext_gemp') else ''
    gemp_fran = "10% mini 15 000 000" if data.get('ext_gemp') else ''
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Tempete, Ouragan, Cyclone, GEMP inondation"), 
                        clean_text(gemp_statut), 
                        clean_text(gemp_cap if gemp_cap else format_amount_fr(data.get('montant', 0))), 
                        clean_text(gemp_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Frais de déblai
    deblai_statut = "Garanti" if data.get('ext_deblais') else "Exclu"
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Frais de deblai et demolition"), 
                        clean_text(deblai_statut), 
                        clean_text("5% de l'indemnite" if data.get('ext_deblais') else ''), 
                        clean_text("Neant" if data.get('ext_deblais') else '')],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # II- RC + RC CROISEE
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font(font_name, "B", 9)
    rc_title = "RC + RC CROISEE"
    pdf.cell(col1_w + col2_w + col3_w + col4_w, 6, clean_text(rc_title), 1, 1, 'L', fill=True)
    
    pdf.set_font(font_name, "", 7)
    
    # Statut RC
    rc_statut = "Garanti" if data.get('ext_rc') else "Exclu"
    rc_cap = data.get('rc_capitaux', '') if data.get('ext_rc') else ''
    rc_fran = data.get('rc_franchises', '') if data.get('ext_rc') else ''
    
    # Ligne 2: Tous Dommages confondus dont
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Tous Dommages confondus dont"), "", clean_text(rc_cap if rc_cap else ''), ""],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Ligne 3: Dommages matériels et immatériels consécutifs
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("- Dommages materiels et immateriels consecutifs avec un capital epuisable pour la duree des travaux"),
                        clean_text("Garanti" if data.get('ext_rc') else "Exclu"),
                        clean_text("500 000 000" if data.get('ext_rc') else ''),
                        ""],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    # Ligne 4: Vol par préposés au préjudice des tiers
    vol_prep_statut = "Garanti" if data.get('ext_vol_preposes') else "Exclu"
    vol_prep_cap = data.get('vol_preposes_capitaux', '') if data.get('ext_vol_preposes') else ''
    vol_prep_fran = data.get('vol_preposes_franchises', '') if data.get('ext_vol_preposes') else ''
    
    vol_cap_text = ""
    if data.get('ext_vol_preposes'):
        vol_cap_text = clean_text("10% des dommages materiels dans la limite de 50 000 000")
    
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("- Vol par preposes au prejudice des tiers"),
                        clean_text(vol_prep_statut),
                        vol_cap_text,
                        ""],
                       height=5,
                       align=['L', 'C', 'C', 'C'])
    
    # Ligne 5: Défense et Recours
    defense_statut = "Garanti" if data.get('ext_defense_recours') else "Exclu"
    defense_cap = data.get('defense_recours_capitaux', '') if data.get('ext_defense_recours') else ''
    defense_fran = data.get('defense_recours_franchises', '') if data.get('ext_defense_recours') else ''
    
    table_row_multicell(pdf, 
                       [col1_w, col2_w, col3_w, col4_w],
                       [clean_text("Defense et Recours"),
                        clean_text(defense_statut),
                        clean_text(defense_cap if defense_cap else "1 000 000"),
                        clean_text(defense_fran)],
                       height=5,
                       align=['L', 'C', 'R', 'C'])
    
    pdf.ln(5)
    
    # ============================================================
    # SECTION 5 : EXCLUSIONS (Vérification de la Correction Robuste)
    # ============================================================
    
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("5.    EXCLUSIONS"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 9)
    pdf.multi_cell(0, 5, clean_text("En plus des exclusions habituelles, sont egalement exclus :"), 0, 'L')
    pdf.ln(2)
    
    # Utilisation du contenu du champ exclusions (passé via data)
    exclusions_content = data.get('exclusions_spe', EXCLUSIONS_DEFAUT)
    exclusions_list = [line.strip() for line in exclusions_content.split('\n') if line.strip()]
    
    pdf.set_font(font_name, "", 8)
    
    # Paramètres de largeur pour la correction de l'erreur FPDF
    puce_indent = 5 # Indentation pour la puce (x)

    for exclusion in exclusions_list:
        
        # Enlever le tiret si l'utilisateur l'a laissé
        if exclusion.startswith('- '):
            exclusion = exclusion[2:] 
        
        # 1. On se repositionne à la marge gauche (par défaut)
        pdf.set_x(pdf.l_margin) 
        
        # 2. On affiche le tiret dans une petite cellule qui ne fait PAS de saut de ligne (ln=0)
        pdf.cell(puce_indent, 5, "-", 0, 0, 'L') 
        
        # 3. On affiche le texte restant dans une multi_cell (0 pour la largeur prend le reste de la ligne).
        pdf.multi_cell(0, 5, clean_text(exclusion), 0, 'L')
    
    pdf.ln(5)
    
    # SECTION 6 : DOCUMENTS À TRANSMETTRE
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("6.    DOCUMENTS A TRANSMETTRE"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 9)
    pdf.set_text_color(255, 0, 0)
    pdf.multi_cell(0, 5, clean_text("La presente offre est soumise au prospect sous reserve de la transmission obligatoire des documents suivants avant souscription :"), 0, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    documents_list = [
        "Cahier des Clauses Techniques et Particulieres (CCTP)",
        "Planning detaille des travaux",
        "Descriptif technique des travaux",
        "Rapport geotechnique (Etude de sol)",
    ]
    
    pdf.set_font(font_name, "", 8)
    for doc in documents_list:
        pdf.cell(10, 5, "_", 0, 0, 'L')
        pdf.cell(0, 5, clean_text(doc), 0, 1, 'L')
    
    pdf.ln(5)
    
    # SECTION 7 : CLAUSES À JOINDRE AU CONTRAT
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, clean_text("7.    CLAUSES A JOINDRE AU CONTRAT"), 0, 1, 'L')
    pdf.ln(2)
    
    clauses_list = [
        "Installations de lutte contre les Incendies (clause C01)",
        "Conditions speciales concernant les mesures de securite contre les pluies, ruissellements et inondations (clause C06)",
        "Maintenance etendue (clause A06)",
        "Garantie heures supplementaires et expeditions a grande Vitesse (A11)",
        "Transport Terrestre (A13)",
        "Responsabilite Civile Croisee (clause A17)",
        "Planning des travaux (Clause B14)",
        "Mesures de securite contre les pluies, ruissellements et inondations (clause C06)",
        "Garantie des biens adjacents et/ou des biens existants (Clause A20)",
        "Garantie des Baraquements et Entrepots de chantier (Clause A22)",
    ]
    
    pdf.set_font(font_name, "", 8)
    for clause in clauses_list:
        pdf.cell(10, 5, "_", 0, 0, 'L')
        pdf.cell(0, 5, clean_text(clause), 0, 1, 'L')
    
    pdf.ln(5)
    
    # Note finale
    pdf.set_font(font_name, "B", 9)
    pdf.set_text_color(255, 0, 0)
    note_finale = "NB : La presente offre est soumise au prospect sous reserve du placement en reassurance facultative de l'excedent de capitaux sur cette affaire."
    pdf.multi_cell(0, 5, clean_text(note_finale), 0, 'L')
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(10)
    
    # Signature
    pdf.set_font(font_name, "", 10)
    pdf.cell(0, 6, "", 0, 1, 'R')
    pdf.set_font(font_name, "B", 10)
    pdf.cell(0, 6, clean_text("Alcide Kouassi"), 0, 1, 'R')
    pdf.cell(0, 6, clean_text("Responsable Souscription"), 0, 1, 'R')
    pdf.cell(0, 6, clean_text("LEADWAY Assurance"), 0, 1, 'R')
    
    # Compatible avec fpdf2
    pdf_output = pdf.output()
    if isinstance(pdf_output, bytes):
        return pdf_output
    else:
        return pdf_output.encode('latin-1')


# =========================================================
# INITIALISATION SESSION STATE
# =========================================================
if 'equipements' not in st.session_state:
    st.session_state.equipements = []

# =========================================================
# INTERFACE PRINCIPALE
# =========================================================

st.title("🏗️ Cotation TRC - Assur Defender")
st.markdown("**Tous Risques Chantier** - Outil de tarification")

# Section 1 : Informations générales
st.markdown('<div class="section-title">1. Informations générales</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    souscripteur = st.text_input("Souscripteur")
    proposant = st.text_input("Proposant")
    intermediaire = st.text_input("Intermédiaire")
    entreprise_principale = st.text_input("Entreprise principale")

with col2:
    maitre_ouvrage = st.text_input("Maître d'ouvrage")
    maitrise_oeuvre = st.text_input("Maîtrise d'œuvre")
    bureau_controle = st.text_input("Bureau de contrôle")
    labo_geotechnique = st.text_input("Laboratoire géotechnique")

autres_intervenants = st.text_area("Autres intervenants", height=100)

# Section 2 : Nature des travaux
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">2. Nature des travaux</div>', unsafe_allow_html=True)

nature_travaux = st.text_area("Description des travaux", height=150)
situation_geo = st.text_area("Situation géographique", height=100)

# Section 3 : Période et durée
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">3. Période et durée des travaux</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    debut_travaux = st.date_input("Début des travaux", datetime.date.today())
with col2:
    fin_travaux = st.date_input("Fin des travaux", datetime.date.today() + datetime.timedelta(days=365))
with col3:
    duree = st.number_input("Durée (mois)", min_value=1, max_value=60, value=12)

# Maintenance et essai
col1, col2 = st.columns(2)
with col1:
    maintenance_incluse = st.checkbox("Maintenance incluse")
    if maintenance_incluse:
        periode_maintenance = st.text_input("Période de maintenance")
    else:
        periode_maintenance = None

with col2:
    essai_inclus = st.checkbox("Essai inclus")
    if essai_inclus:
        periode_essai = st.text_input("Période d'essai")
    else:
        periode_essai = None

# Section 4 : Type de travaux et montant
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">4. Type de travaux et montant</div>', unsafe_allow_html=True)

type_travaux = st.selectbox(
    "Type de travaux",
    ["Bâtiment", "Assainissement", "Route"]
)

montant = st.number_input(
    "Montant des travaux (FCFA)",
    min_value=0,
    value=100000000,
    step=1000000,
    format="%d"
)

# Champs spécifiques pour les bâtiments
if type_travaux == "Bâtiment":
    usage_display = st.selectbox(
        "Usage du bâtiment",
        ["Logement ou commercial", "Public ou industriel"]
    )
    usage_key = "logement_commercial" if "Logement" in usage_display else "public_industriel"
    
    structure_display = st.selectbox("Structure", list(STRUCTURE_OPTIONS.keys()))
    structure = STRUCTURE_OPTIONS[structure_display]
else:
    usage_key = None
    structure = None

# Section 5 : Franchise
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">5. Franchise</div>', unsafe_allow_html=True)

franchise_key = st.selectbox("Franchise", list(FRANCHISE_COEF.keys()))

# Section 6 : Extensions de garantie
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">6. Extensions de garantie</div>', unsafe_allow_html=True)

st.markdown('<div class="section-subtitle">Extensions standards (incluses automatiquement)</div>', unsafe_allow_html=True)
ext_maintenance = st.checkbox("A05 - Maintenance Visite (10% de la prime travaux)", value=True)
ext_deblais = st.checkbox("Déblais, démolition et frais de déblaiement (+0.15‰)", value=True)

st.markdown('<div class="section-subtitle">Extension DOMMAGES DIRECTS À L\'OUVRAGE</div>', unsafe_allow_html=True)

# Nouvelles extensions
ext_honoraires_expert = st.checkbox("Honoraires d'expert")
if ext_honoraires_expert:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        honoraires_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="honoraires_capitaux")
    with col2:
        honoraires_franchises = st.text_input("Franchises (FCFA)", value="", key="honoraires_franchises")
    st.markdown("---")
else:
    honoraires_capitaux = ""
    honoraires_franchises = ""

ext_erreur_conception = st.checkbox("Erreur de conception (Y compris parties viciées)")
if ext_erreur_conception:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        erreur_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="erreur_capitaux")
    with col2:
        erreur_franchises = st.text_input("Franchises (FCFA)", value="", key="erreur_franchises")
    st.markdown("---")
else:
    erreur_capitaux = ""
    erreur_franchises = ""

ext_heures_suppl = st.checkbox("Heures supplémentaires, Travail de nuit, Transport à grande vitesse")
if ext_heures_suppl:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        heures_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="heures_capitaux")
    with col2:
        heures_franchises = st.text_input("Franchises (FCFA)", value="", key="heures_franchises")
    st.markdown("---")
else:
    heures_capitaux = ""
    heures_franchises = ""

ext_vol_entrepose = st.checkbox("Vol des biens entreposés hors chantier")
if ext_vol_entrepose:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        vol_entrepose_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="vol_entrepose_capitaux")
    with col2:
        vol_entrepose_franchises = st.text_input("Franchises (FCFA)", value="", key="vol_entrepose_franchises")
    st.markdown("---")
else:
    vol_entrepose_capitaux = ""
    vol_entrepose_franchises = ""

ext_transport_terrestre = st.checkbox("Transport terrestre")
if ext_transport_terrestre:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        transport_terrestre_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="transport_terrestre_capitaux")
    with col2:
        transport_terrestre_franchises = st.text_input("Franchises (FCFA)", value="", key="transport_terrestre_franchises")
    st.markdown("---")
else:
    transport_terrestre_capitaux = ""
    transport_terrestre_franchises = ""

ext_transport_aerien = st.checkbox("Transport aérien")
if ext_transport_aerien:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        transport_aerien_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="transport_aerien_capitaux")
    with col2:
        transport_aerien_franchises = st.text_input("Franchises (FCFA)", value="", key="transport_aerien_franchises")
    st.markdown("---")
else:
    transport_aerien_capitaux = ""
    transport_aerien_franchises = ""

ext_conduits_souterrains = st.checkbox("Conduits et Souterrains")
if ext_conduits_souterrains:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        conduits_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="conduits_capitaux")
    with col2:
        conduits_franchises = st.text_input("Franchises (FCFA)", value="", key="conduits_franchises")
    st.markdown("---")
else:
    conduits_capitaux = ""
    conduits_franchises = ""

ext_existants = st.checkbox("A20 - Dommages aux Existants (20% du montant travaux)")
if ext_existants:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        existants_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="existants_capitaux")
    with col2:
        existants_franchises = st.text_input("Franchises (FCFA)", value="", key="existants_franchises")
    st.markdown("---")
else:
    existants_capitaux = ""
    existants_franchises = ""

# Section RC + RC croisée
st.markdown('<div class="section-subtitle">RC + RC croisée</div>', unsafe_allow_html=True)

ext_rc = st.checkbox("A17 - Responsabilité civile")

if ext_rc:
    st.markdown("**Paramètres A17 - Responsabilité civile:**")
    col1, col2 = st.columns(2)
    with col1:
        rc_suppl_trafic_key = st.selectbox(
            "Supplément trafic",
            list(RC_SUPPLEMENTS["trafic"].keys())
        )
    with col2:
        rc_suppl_prox_key = st.selectbox(
            "Supplément proximité bâtiments",
            list(RC_SUPPLEMENTS["proximite"].keys())
        )
    ext_rc_croisee = st.checkbox("RC Croisée (+10%)")
    
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        rc_capitaux_garantis = st.text_input("Capitaux Garantis (FCFA)", value="", key="rc_capitaux")
    with col2:
        rc_franchises = st.text_input("Franchises (FCFA)", value="", key="rc_franchises")
    st.markdown("---")
else:
    rc_suppl_trafic_key = "Non applicable"
    rc_suppl_prox_key = "Non applicable"
    ext_rc_croisee = False
    rc_capitaux_garantis = ""
    rc_franchises = ""

ext_vol_preposes = st.checkbox("Vol par préposés au préjudice des tiers")
if ext_vol_preposes:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        vol_preposes_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="vol_capitaux")
    with col2:
        vol_preposes_franchises = st.text_input("Franchises (FCFA)", value="", key="vol_franchises")
    st.markdown("---")
else:
    vol_preposes_capitaux = ""
    vol_preposes_franchises = ""

ext_defense_recours = st.checkbox("Défense et Recours")
if ext_defense_recours:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        defense_recours_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="defense_capitaux")
    with col2:
        defense_recours_franchises = st.text_input("Franchises (FCFA)", value="", key="defense_franchises")
    st.markdown("---")
else:
    defense_recours_capitaux = ""
    defense_recours_franchises = ""

# Extensions nécessitant validation DT
st.markdown('<div class="section-subtitle">Extensions nécessitant validation Direction Technique</div>', unsafe_allow_html=True)

ext_maint_etendue = st.checkbox("A06 - Maintenance étendue (Validation DT requise)")
if ext_maint_etendue:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        maint_etendue_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="maint_etendue_capitaux")
    with col2:
        maint_etendue_franchises = st.text_input("Franchises (FCFA)", value="", key="maint_etendue_franchises")
    
    prime_maint_etendue = st.number_input(
        "Prime A06 - Maintenance étendue (FCFA)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        key="prime_maint_etendue"
    )
    st.markdown("---")
else:
    maint_etendue_capitaux = ""
    maint_etendue_franchises = ""
    prime_maint_etendue = 0.0

ext_maint_const = st.checkbox("A07 - Maintenance constructeur (Validation DT requise)")
if ext_maint_const:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        maint_const_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="maint_const_capitaux")
    with col2:
        maint_const_franchises = st.text_input("Franchises (FCFA)", value="", key="maint_const_franchises")
    
    prime_maint_const = st.number_input(
        "Prime A07 - Maintenance constructeur (FCFA)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        key="prime_maint_const"
    )
    st.markdown("---")
else:
    maint_const_capitaux = ""
    maint_const_franchises = ""
    prime_maint_const = 0.0

ext_materiel = st.checkbox("A21 - Matériel et installations de chantier (Validation DT requise)")
if ext_materiel:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        materiel_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="materiel_capitaux")
    with col2:
        materiel_franchises = st.text_input("Franchises (FCFA)", value="", key="materiel_franchises")
    
    prime_materiel = st.number_input(
        "Prime A21 - Matériel et installations (FCFA)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        key="prime_materiel"
    )
    st.markdown("---")
else:
    materiel_capitaux = ""
    materiel_franchises = ""
    prime_materiel = 0.0

ext_baraquement = st.checkbox("A22 - Baraquements provisoires (Validation DT requise)")
if ext_baraquement:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        baraquement_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="baraquement_capitaux")
    with col2:
        baraquement_franchises = st.text_input("Franchises (FCFA)", value="", key="baraquement_franchises")
    
    prime_baraquement = st.number_input(
        "Prime A22 - Baraquements provisoires (FCFA)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        key="prime_baraquement"
    )
    st.markdown("---")
else:
    baraquement_capitaux = ""
    baraquement_franchises = ""
    prime_baraquement = 0.0

ext_gemp = st.checkbox("FANAF01 - Garantie Environnement Modification Paysagère (Validation DT requise)")
if ext_gemp:
    st.markdown("**Capitaux et Franchises:**")
    col1, col2 = st.columns(2)
    with col1:
        gemp_capitaux = st.text_input("Capitaux Garantis (FCFA)", value="", key="gemp_capitaux")
    with col2:
        gemp_franchises = st.text_input("Franchises (FCFA)", value="", key="gemp_franchises")
    
    prime_gemp = st.number_input(
        "Prime FANAF01 - Garantie Environnement (FCFA)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        key="prime_gemp"
    )
    st.markdown("---")
else:
    gemp_capitaux = ""
    gemp_franchises = ""
    prime_gemp = 0.0

# Section 7 : Équipements et installations (A21/A22)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">7. Équipements et installations de chantier</div>', unsafe_allow_html=True)

if ext_materiel or ext_baraquement:
    st.info("ℹ️ Cette section nécessite la validation de la Direction Technique.")
    
    # Gestion des équipements
    st.markdown('<div class="section-subtitle">Ajouter un équipement</div>', unsafe_allow_html=True)
    
    type_equipement = st.selectbox(
        "Type d'équipement",
        ["Grue à tour", "Grue automobile", "Bulldozers, niveleuses, scrapers", 
         "Chargeurs, dumpers", "Compacteurs vibrants", "Sonnettes / extracteurs de pieux",
         "Rouleaux compresseurs", "Locomotives de chantier", "Baraquement de stockage",
         "Bureaux provisoires de chantier"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        valeur_equipement = st.number_input("Valeur à neuf (FCFA)", min_value=0, value=10000000, step=1000000)
    with col2:
        duree_equipement = st.selectbox("Durée (mois)", list(range(1, 13)))
    
    # Champs spécifiques selon le type
    if type_equipement == "Grue à tour":
        hauteur_grue = st.selectbox("Hauteur grue", ["< 30M", "> 30M"])
        classe_grue = st.selectbox("Classe", ["Classe 1", "Classe 2", "Classe 3"])
    elif type_equipement in TARIFS_ENGINS:
        hauteur_grue = None
        classe_grue = st.selectbox("Classe", ["Classe 1", "Classe 2", "Classe 3"])
    else:
        hauteur_grue = None
        classe_grue = None
    
    franchise_equipement = st.selectbox(
        "Franchise",
        list(RABAIS_FRANCHISE_EQUIPEMENTS.keys())
    )
    
    if st.button("➕ Ajouter l'équipement"):
        equipement = {
            "type": type_equipement,
            "valeur": valeur_equipement,
            "duree": duree_equipement,
            "hauteur": hauteur_grue,
            "classe": classe_grue,
            "franchise": franchise_equipement
        }
        st.session_state.equipements.append(equipement)
        st.success("✅ Équipement ajouté!")
    
    # Affichage des équipements
    if st.session_state.equipements:
        st.markdown('<div class="section-subtitle">Équipements ajoutés</div>', unsafe_allow_html=True)
        
        for idx, eq in enumerate(st.session_state.equipements):
            col1, col2 = st.columns([4, 1])
            with col1:
                details = f"**{eq['type']}** - {eq['valeur']:,.0f}".replace(",", " ") + f" FCFA - {eq['duree']} mois"
                if eq['classe']:
                    details += f" - {eq['classe']}"
                if eq['hauteur']:
                    details += f" - {eq['hauteur']}"
                st.write(details)
            with col2:
                if st.button("🗑️ Supprimer", key=f"del_{idx}"):
                    st.session_state.equipements.pop(idx)
                    st.rerun()
    
    # Calcul de la prime équipements
    prime_totale_equipements = 0
    for eq in st.session_state.equipements:
        # Déterminer le taux annuel
        if eq['type'] == "Grue à tour":
            taux_annuel = TARIFS_GRUES_TOUR[eq['hauteur']][eq['classe']]
        elif eq['type'] in TARIFS_ENGINS:
            taux_annuel = TARIFS_ENGINS[eq['type']][eq['classe']]
        else:
            taux_annuel = TARIFS_BARAQUEMENTS[eq['type']]
        
        # Appliquer le coefficient de durée
        coef_duree = COEF_DUREE_EQUIPEMENTS[eq['duree']]
        taux_ajuste = taux_annuel * coef_duree
        
        # Appliquer le rabais franchise
        rabais_franchise = RABAIS_FRANCHISE_EQUIPEMENTS[eq['franchise']]
        taux_final = taux_ajuste * rabais_franchise
        
        # Calculer la prime
        prime_eq = calc_prime(eq['valeur'], taux_final)
        prime_totale_equipements += prime_eq
else:
    prime_totale_equipements = 0

# =========================================================
# Section 8 : Exclusions et Mode manuel (Intégration du nouveau champ)
# =========================================================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">8. Exclusions et Mode de tarification</div>', unsafe_allow_html=True)

# NOUVEAU CHAMP D'EXCLUSIONS
exclusions_spe = st.text_area(
    "Exclusions spécifiques (une exclusion par ligne)",
    value=EXCLUSIONS_DEFAUT,
    height=250
)

st.markdown('<div class="section-subtitle">Mode de tarification</div>', unsafe_allow_html=True)

# Vérifications pour information uniquement
montant_depasse = montant > 2000000000

extensions_dt = ext_maint_etendue or ext_maint_const or ext_materiel or ext_baraquement or ext_gemp

# Affichage des informations (non bloquantes)
if montant_depasse:
    st.info("ℹ️ Le montant dépasse 2 milliards FCFA - Vous pouvez continuer avec le calcul automatique ou utiliser la tarification manuelle.")
if extensions_dt:
    st.info("ℹ️ Des extensions nécessitant validation DT sont sélectionnées. N'oubliez pas de saisir les primes correspondantes.")

# Mode manuel
mode_manuel = st.checkbox("Activer la tarification manuelle (hors barème)")

if mode_manuel:
    raison_manuel = st.radio(
        "Raison de la tarification manuelle",
        ["montant_eleve", "validation_dt", "volontaire"],
        format_func=lambda x: {
            "montant_eleve": "Montant > 2 milliards FCFA",
            "validation_dt": "Extensions nécessitant validation DT",
            "volontaire": "Choix volontaire (hors barème)"
        }[x]
    )
    
    st.markdown('<div class="section-subtitle">Saisie manuelle des primes</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        prime_nette_manuelle = st.number_input(
            "Prime nette (FCFA)",
            min_value=0.0,
            value=0.0,
            step=10000.0
        )
    with col2:
        accessoires_manuels = st.number_input(
            "Accessoires (FCFA)",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )
else:
    raison_manuel = None
    prime_nette_manuelle = 0
    accessoires_manuels = 0

# Le bouton est toujours activé
calcule = st.button("Calculer la prime", type="primary", use_container_width=True)

# Section 9 : Calculs et résultats
if calcule:
    # Fonction de formatage pour l'affichage Streamlit (avec espace comme séparateur)
    def format_st(amount):
        return f"{amount:,.0f}".replace(",", " ")

    if mode_manuel:
        # MODE MANUEL
        prime_nette = prime_nette_manuelle
        accessoires = accessoires_manuels
        taxes = calc_taxes(prime_nette, accessoires)
        prime_ttc = prime_nette + accessoires + taxes
        
        taux_net_travaux = 0
        prime_travaux = 0
        prime_maintenance = 0
        prime_rc = 0
        prime_existants = 0
        taux_rc_final = 0
        
    else:
        # MODE AUTOMATIQUE
        # 1. Taux de base
        taux_base = get_taux_base(type_travaux, duree, usage_key, structure)
        
        # 2. Ajustement franchise
        taux_base_franchise = taux_base * FRANCHISE_COEF[franchise_key]
        
        # 3. Taux net travaux
        taux_net_travaux = taux_base_franchise
        if ext_deblais:
            taux_net_travaux += 0.15
        
        # 4. Prime TRAVAUX
        prime_travaux = calc_prime(montant, taux_net_travaux)
        
        # 5. Prime MAINTENANCE
        prime_maintenance = 0
        if ext_maintenance:
            prime_maintenance_base = calc_prime(montant, taux_base_franchise)
            prime_maintenance = prime_maintenance_base * 0.10
            
        # 6. Prime RC
        prime_rc = 0
        taux_rc_final = 0
        if ext_rc:
            taux_rc_final = calc_taux_rc(
                type_travaux, 
                taux_net_travaux, 
                rc_suppl_trafic_key, 
                rc_suppl_prox_key, 
                ext_rc_croisee
            )
            prime_rc = calc_prime(montant, taux_rc_final)
            
        # 7. Prime EXISTANTS
        prime_existants = 0
        if ext_existants:
            valeur_existants = 0.2 * montant
            taux_existants = taux_net_travaux * 0.5
            prime_existants = calc_prime(valeur_existants, taux_existants)

        # 8. Totaux + Primes extensions DT
        prime_extensions_dt = prime_maint_etendue + prime_maint_const + prime_materiel + prime_baraquement + prime_gemp
        prime_nette = prime_travaux + prime_maintenance + prime_rc + prime_existants + prime_totale_equipements + prime_extensions_dt
        accessoires = calc_accessoires(prime_nette)
        taxes = calc_taxes(prime_nette, accessoires)
        prime_ttc = prime_nette + accessoires + taxes

    # Affichage des résultats
    st.markdown('<div class="section-title">Résultats de la cotation</div>', unsafe_allow_html=True)
    
    if mode_manuel:
        if raison_manuel == "montant_eleve":
            st.info("ℹ️ **Tarification manuelle** (montant > 2 milliards FCFA)")
        elif raison_manuel == "validation_dt":
            st.info("ℹ️ **Tarification manuelle** (extensions nécessitant validation Direction Technique)")
        elif raison_manuel == "volontaire":
            st.info("ℹ️ **Tarification manuelle** (hors barème - choix volontaire)")
    else:
        # Tableau de décomposition
        st.markdown("**Décomposition de la prime**")
        
        decomposition_data = []
        
        decomposition_data.append({
            "Garantie": "Prime Dommages à l'ouvrage (Travaux)",
            "Montant (FCFA)": format_st(prime_travaux),
            "Taux (‰)": f"{taux_net_travaux:.3f}"
        })
        
        if ext_maintenance:
            decomposition_data.append({
                "Garantie": "Prime Maintenance Visite (A05)",
                "Montant (FCFA)": format_st(prime_maintenance),
                "Taux (‰)": "-"
            })
        
        if ext_rc:
            decomposition_data.append({
                "Garantie": "Prime Responsabilité Civile (A17)",
                "Montant (FCFA)": format_st(prime_rc),
                "Taux (‰)": f"{taux_rc_final:.3f}"
            })
        
        if ext_existants:
            decomposition_data.append({
                "Garantie": "Prime Dommages aux Existants (A20)",
                "Montant (FCFA)": format_st(prime_existants),
                "Taux (‰)": f"{taux_net_travaux * 0.5:.3f}"
            })
        
        if prime_totale_equipements > 0:
            decomposition_data.append({
                "Garantie": f"Prime Équipements et Installations (A21/A22) - {len(st.session_state.equipements)} équipement(s)",
                "Montant (FCFA)": format_st(prime_totale_equipements),
                "Taux (‰)": "-"
            })
        
        # Extensions DT
        if ext_maint_etendue and prime_maint_etendue > 0:
            decomposition_data.append({
                "Garantie": "Prime Maintenance étendue (A06)",
                "Montant (FCFA)": format_st(prime_maint_etendue),
                "Taux (‰)": "-"
            })
        
        if ext_maint_const and prime_maint_const > 0:
            decomposition_data.append({
                "Garantie": "Prime Maintenance constructeur (A07)",
                "Montant (FCFA)": format_st(prime_maint_const),
                "Taux (‰)": "-"
            })
        
        if ext_materiel and prime_materiel > 0:
            decomposition_data.append({
                "Garantie": "Prime Matériel et installations (A21)",
                "Montant (FCFA)": format_st(prime_materiel),
                "Taux (‰)": "-"
            })
        
        if ext_baraquement and prime_baraquement > 0:
            decomposition_data.append({
                "Garantie": "Prime Baraquements provisoires (A22)",
                "Montant (FCFA)": format_st(prime_baraquement),
                "Taux (‰)": "-"
            })
        
        if ext_gemp and prime_gemp > 0:
            decomposition_data.append({
                "Garantie": "Prime Garantie Environnement (FANAF01)",
                "Montant (FCFA)": format_st(prime_gemp),
                "Taux (‰)": "-"
            })
        
        df_decomposition = pd.DataFrame(decomposition_data)
        st.dataframe(df_decomposition, use_container_width=True, hide_index=True)
    
    # Total
    st.markdown("**Total**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prime Nette", f"{format_st(prime_nette)} FCFA")
    col2.metric("Accessoires", f"{format_st(accessoires)} FCFA")
    col3.metric("Taxes (14.5%)", f"{format_st(taxes)} FCFA")
    col4.metric("**PRIME TTC**", f"**{format_st(prime_ttc)} FCFA**")

    # Clauses
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Clauses à insérer au contrat</div>', unsafe_allow_html=True)
    
    st.markdown("<h6>Clauses Obligatoires</h6>", unsafe_allow_html=True)
    for clause in CLAUSES["obligatoires"][type_travaux]:
        st.write(f"- {clause}")
        
    st.markdown("<h6>Clauses relatives aux extensions souscrites</h6>", unsafe_allow_html=True)
    clauses_ext_actives = []
    if ext_maintenance: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A05"])
    if ext_rc: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A17"])
    if ext_rc_croisee: 
        clauses_ext_actives.append("A17 (RC Croisée)")
    if ext_existants: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A20"])
    if ext_maint_etendue: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A06"])
    if ext_maint_const: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A07"])
    if ext_materiel: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A21"])
    if ext_baraquement: 
        clauses_ext_actives.append(CLAUSES["extensions"]["A22"])
    if ext_gemp: 
        clauses_ext_actives.append(CLAUSES["extensions"]["FANAF01"])
    
    if clauses_ext_actives:
        for clause in clauses_ext_actives:
            st.write(f"- {clause}")
    else:
        st.info("Aucune extension (A05, A06, A07, A17, A20, A21, A22, FANAF01) n'a été sélectionnée.")
    
    # Bouton de téléchargement PDF
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Télécharger la cotation</div>', unsafe_allow_html=True)
    
    # Préparer les données pour le PDF
    pdf_data = {
        'souscripteur': souscripteur,
        'proposant': proposant,
        'intermediaire': intermediaire,
        'entreprise_principale': entreprise_principale,
        'maitre_ouvrage': maitre_ouvrage,
        'maitrise_oeuvre': maitrise_oeuvre,
        'bureau_controle': bureau_controle,
        'labo_geotechnique': labo_geotechnique,
        'autres_intervenants': autres_intervenants,
        'nature_travaux': nature_travaux,
        'situation_geo': situation_geo,
        'debut_travaux': debut_travaux.strftime('%d/%m/%Y'),
        'fin_travaux': fin_travaux.strftime('%d/%m/%Y'),
        'duree': duree,
        'duree_texte': f"{duree} mois",
        'duree_maintenance': "12 mois" if maintenance_incluse else "N/A",
        'maintenance_incluse': maintenance_incluse,
        'periode_maintenance': periode_maintenance if maintenance_incluse else "N/A",
        'essai_inclus': essai_inclus,
        'periode_essai': periode_essai if essai_inclus else "N/A",
        'montant': montant,
        'montant_f': f"{montant:,.0f}",
        'date_cotation': datetime.date.today().strftime('%d.%m.%Y'),
        'date_demande': datetime.date.today().strftime('%d/%m/%Y'),
        'prime_nette': prime_nette,
        'prime_nette_finale': prime_nette,
        'reduction_commerciale': 0,
        'accessoires': accessoires,
        'taxes': taxes,
        'prime_ttc': prime_ttc,
        # NOUVEAU: Contenu du champ Exclusions
        'exclusions_spe': exclusions_spe,
        # Extensions
        'ext_honoraires_expert': ext_honoraires_expert,
        'honoraires_capitaux': honoraires_capitaux if ext_honoraires_expert else "",
        'honoraires_franchises': honoraires_franchises if ext_honoraires_expert else "",
        'ext_existants': ext_existants,
        'existants_capitaux': existants_capitaux if ext_existants else "",
        'existants_franchises': existants_franchises if ext_existants else "",
        'ext_erreur_conception': ext_erreur_conception,
        'erreur_capitaux': erreur_capitaux if ext_erreur_conception else "",
        'erreur_franchises': erreur_franchises if ext_erreur_conception else "",
        'ext_heures_suppl': ext_heures_suppl,
        'heures_capitaux': heures_capitaux if ext_heures_suppl else "",
        'heures_franchises': heures_franchises if ext_heures_suppl else "",
        'ext_vol_entrepose': ext_vol_entrepose,
        'vol_entrepose_capitaux': vol_entrepose_capitaux if ext_vol_entrepose else "",
        'vol_entrepose_franchises': vol_entrepose_franchises if ext_vol_entrepose else "",
        'ext_transport_terrestre': ext_transport_terrestre,
        'transport_terrestre_capitaux': transport_terrestre_capitaux if ext_transport_terrestre else "",
        'transport_terrestre_franchises': transport_terrestre_franchises if ext_transport_terrestre else "",
        'ext_transport_aerien': ext_transport_aerien,
        'transport_aerien_capitaux': transport_aerien_capitaux if ext_transport_aerien else "",
        'transport_aerien_franchises': transport_aerien_franchises if ext_transport_aerien else "",
        'ext_conduits_souterrains': ext_conduits_souterrains,
        'conduits_capitaux': conduits_capitaux if ext_conduits_souterrains else "",
        'conduits_franchises': conduits_franchises if ext_conduits_souterrains else "",
        'ext_baraquement': ext_baraquement,
        'baraquement_capitaux': baraquement_capitaux if ext_baraquement else "",
        'baraquement_franchises': baraquement_franchises if ext_baraquement else "",
        'ext_gemp': ext_gemp,
        'gemp_capitaux': gemp_capitaux if ext_gemp else "",
        'ext_deblais': ext_deblais,
        'ext_materiel': ext_materiel,
        'ext_rc': ext_rc,
        'rc_capitaux': rc_capitaux_garantis if ext_rc else "",
        'rc_franchises': rc_franchises if ext_rc else "",
        'ext_vol_preposes': ext_vol_preposes,
        'vol_preposes_capitaux': vol_preposes_capitaux if ext_vol_preposes else "",
        'vol_preposes_franchises': vol_preposes_franchises if ext_vol_preposes else "",
        'ext_defense_recours': ext_defense_recours,
        'defense_recours_capitaux': defense_recours_capitaux if ext_defense_recours else "",
        'defense_recours_franchises': defense_recours_franchises if ext_defense_recours else "",
    }
    
    # Générer le PDF
    pdf_bytes = generate_pdf(pdf_data)
    
    # Bouton de téléchargement
    st.download_button(
        label="📥 Télécharger la cotation PDF",
        data=pdf_bytes,
        file_name=f"Cotation_TRC_{souscripteur.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
