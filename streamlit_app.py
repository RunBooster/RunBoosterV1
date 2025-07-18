import streamlit as st
import pandas as pd
import random
import smtplib
import numpy as np
from fpdf import FPDF
import os
from email.message import EmailMessage

produits = "produits.xlsx"  
df = pd.read_excel(produits, sheet_name="Produits énergétiques", engine="openpyxl")

left, middle =st.columns([1,3], vertical_alignment="bottom")
left.image("RunBooster(1).png", width=100) 
middle.subheader("Boost ton run grâce à une alimentation controlée")
st.divider()

def load_data():
    df = pd.read_excel("produits.xlsx")  # Remplace par ton fichier
    df["Marque"] = df["Marque"].astype(str) # Convertir toutes les valeurs en string
    df["Nom"] = df["Nom"].astype(str)     
    return df
df = load_data()
df = df[~((df['Ref'] == 'B') & (df['Masse'] == 1) & (df['Sodium'] > 0.0125))] #on enlève les boissons en pot trop riches en sodium
df = df[~((df["Ref"] == 'B') & (df["Caf"] != 0))]
eau=500

proposition = []

discipline = st.radio("Choisi ta discipline 👇", ["Trail", "Course sur route / Vélo"], horizontal=True)
distance = st.number_input("Entre la distance de ta course en km", format="%0.1f")

if discipline=="Trail":
     cote = st.number_input("Entre ta cote ITRA ou UTMB Index", min_value=1, value=500)
     deniv = st.number_input("Entre le dénivelé positif en m", format="%0f")
     disteff=(distance+(deniv/100))
     tpsestime=1000*(0.00000006964734390393*(disteff)*(disteff)*(disteff)*(disteff)-0.00006550491191697*(disteff)*(disteff)*(disteff)+0.020181800970007*(disteff)*(disteff)+2.20983621768921*(disteff))/cote
     proposition.append(f"Plan nutritionnel pour ton trail de {distance} kms et {deniv} m de dénivelé, avec une cote de {cote},")
else:
     st.write("Entre ton temps de course estimé 👇")
     tpsh=st.number_input("Heures", min_value=0)
     tpsm=st.number_input("Minutes", min_value=0, max_value=59)
     tpsestime=(tpsh*60)+tpsm
     cote=700
     proposition.append(f"Plan nutritionnel pour ta course de {distance} kms,")
tpsestimeh=tpsestime/60
st.write('➜Temps de course estimé:', int(tpsestime), 'minutes, soit', int(tpsestimeh), 'h', int((tpsestimeh%1)*60), 'min' )
proposition.append(f"pour un temps estimé de {int(tpsestime)} minutes, soit {int(tpsestimeh)}h {int((tpsestimeh % 1) * 60)} min :")

objectif=st.radio("Choisi ton objectif 👇", ["Performance", "Plaisir", "Finisher"], horizontal=True)
if objectif=="Performance" and tpsestimeh<1:
        cas=1
        Cho=0
        cafeine=1
        #st.write("Tu consommeras un peu de boisson d'effort à l'échauffement, et un petit gel 5min avant le départ.")
        proposition.append("Tu consommeras un peu de boisson d'effort à l'échauffement, avec éventuellement une 100aine de mg de caféine, et un petit gel 5min avant le départ.")
elif objectif!="Performance" and tpsestimeh<1:
        cas=1
        Cho=0
        cafeine=0
        #st.write('Tu consommeras une compote sucrée 5min avant le départ.')
        proposition.append('Tu consommeras une compote sucrée 5min avant le départ.')
elif (objectif=="Performance" or objectif=="Plaisir") and 1<=tpsestimeh<2:
        Cho=45
        cas=2
        cafeine=1
elif objectif=="Performance" and 2<=tpsestimeh<3:
        Cho=70
        cas=4
        cafeine=1
        df = df[~(df["Ref"].isin(["BA","BAS","BS", "CS"]))]
elif objectif=="Performance" and 3<=tpsestimeh<5:
        Cho=80
        cas=6
        cafeine=1
        df = df[~(df["Ref"].isin(["BS"]))]
elif objectif=="Performance" and tpsestimeh>=5 and cote<620:
        Cho=70
        cas=7
        cafeine=1
elif objectif=="Performance" and tpsestimeh>=5:
        Cho=85
        cas=7
        cafeine=1
elif objectif=="Plaisir" and tpsestimeh>=2:
        Cho=60
        cas=5
        cafeine=0   
        df = df[~(df["Ref"].isin(["G"]))]
else:
        cas=3
        Cho=40
        cafeine=0
        df = df[~(df["Ref"].isin(["G"]))]
        df = df[~((df["Ref"] == "B") & ~df["Nom"].fillna("").str.startswith(("Jus", "Sirop")))]

     
if objectif=="Performance" and 3<=tpsestimeh:
     values = list(range(60, 91))
     Cho_indiv = st.select_slider(
        "Modifie ta consomation de glucides (g/h) si tu la penses trop haute, ou laisse la valeur par défaut:",
        options=values,
        value=Cho)
     Cho=Cho_indiv
     
st.write("Tu consommeras", (Cho), "g de glucides par heure de course")
Chotot=Cho*tpsestimeh
#st.write('➜Tu consommeras', Cho,'g de glucides par heure, soit', int(Chotot), 'grammes de glucides sur la course')
proposition.append(f"➜Tu consommeras {Cho}g de glucides par heure, soit {int(Chotot)} grammes de glucides sur la course.")
temp=st.checkbox("Cocher si plus de 20°C annoncés")
st.divider()
if temp and tpsestimeh>=2:
        #st.write('➜Tu ajouteras dans ta gourde, 1g de sel de table par heure de course, pour compenser tes pertes en sodium')
        proposition.append('➜Tu ajouteras un peu de sel de table dans ta gourde, pour un apport de Sodium total de 400mg par heure de course (1g de sel de table=400mg de Sodium), pour compenser tes pertes en sodium.')
        if tpsestimeh>=3:
            eau=700
if objectif=="Performance" and tpsestimeh>=5:
        #st.write('➜Tu peux ajouter dans ta gourde, 3g de BCAA 2.1.1 par heure de course, pour limiter les fatigues musculaire et nerveuse')
        proposition.append('➜Option facultative: tu peux ajouter dans ta gourde, 2g de BCAA 2.1.1 par heure de course, pour limiter les fatigues musculaire et nerveuse.')

# Liste des marques uniques 
marques = sorted(df["Marque"].dropna().unique().tolist(), key=str)
# Sélection multiple des marques
selection = st.multiselect("Quelles sont tes marques de nutrition préférées? 👇", marques)
st.write("Laisse la case vide si tu veux laisser RunBooster choisir pour toi." )

gout = st.multiselect("Des goûts que tu n'aimes pas? 👇",
    ["Chocolat", "Vanille", "Café", "Fruits rouges", "Menthe", "Citron", "Agrumes", "Figue", "Raisin", "Banane", "Kiwi", "Ananas", "Pomme", "Peche", "Abricot", "Cranberries", "Pruneaux", "Cerise", "Amande", "Noisette", "Cacahuete","Noix de coco", "Caramel", "Patate douce", "Petits pois", "Carotte", "Betterave", "Olive"])
if "Chocolat" in gout:
    df = df[~(df['Nom'].str.contains("Choc|Cacao", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Fruits rouges" in gout:
    df = df[~(df['Nom'].str.contains("Fruits Rouges|fruits rouges|Fraise|Framboise|Cassis|Myrtille|Mure|Cranberrie|Canneberge|Cranberry", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Menthe" in gout:
    df = df[~(df['Nom'].str.contains("Menthe|Mint", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Citron" in gout:
    df = df[~(df['Nom'].str.contains("Citron|Lemon|Citrus", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Agrumes" in gout:
    df = df[~(df['Nom'].str.contains("Agrum|Citron|Mandar|Orang|Pamplem|Pomelo", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Figue" in gout:
    df = df[~(df['Nom'].str.contains("Fig", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Raisin" in gout:
    df = df[~(df['Nom'].str.contains("Raisin|Grape", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Banane" in gout:
    df = df[~(df['Nom'].str.contains("Banan", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Kiwi" in gout:
    df = df[~(df['Nom'].str.contains("Kiwi", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Ananas" in gout:
    df = df[~(df['Nom'].str.contains("Anana|Pineapple", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Pomme" in gout:
    df = df[~(df['Nom'].str.contains("Pomme|Apple", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Peche" in gout:
    df = df[~(df['Nom'].str.contains("Peche|Peach", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Abricot" in gout:
    df = df[~(df['Nom'].str.contains("Abricot|Apricot", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Cranberries" in gout:
    df = df[~(df['Nom'].str.contains("Cranberrie|Canneberge|Cranberry", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Pruneaux" in gout:
    df = df[~(df['Nom'].str.contains("Prune", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Cerise" in gout:
    df = df[~(df['Nom'].str.contains("Cerise|Cherry", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Amande" in gout:
    df = df[~(df['Nom'].str.contains("Amande|Almond", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Noisette" in gout:
    df = df[~(df['Nom'].str.contains("Noisette|Hazelnut", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Cacahuete" in gout:
    df = df[~(df['Nom'].str.contains("Cacahuete|Peanut", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Noix de coco" in gout:
    df = df[~(df['Nom'].str.contains(" Coco", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Caramel" in gout:
    df = df[~(df['Nom'].str.contains("Caramel", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Patate douce" in gout:
    df = df[~(df['Nom'].str.contains("Patate|Potato", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Petits pois" in gout:
    df = df[~(df['Nom'].str.contains("Pois|Peas", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Carotte" in gout:
    df = df[~(df['Nom'].str.contains("Carot", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Betterave" in gout:
    df = df[~(df['Nom'].str.contains("Betterave|Beet", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Olive" in gout:
    df = df[~(df['Nom'].str.contains("Olive", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Vanille" in gout:
    df = df[~(df['Nom'].str.contains("Vanill", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]
if "Café" in gout:
    df = df[~(df['Nom'].str.contains("Café|Coffe", case=False, na=False) & ~df['Nom'].str.contains(" ou ", case=False, na=False))]


st.write("As-tu des critères? 👇")
filtrer_bio = st.checkbox("Produits Bio")
filtrer_noix = st.checkbox("Sans fruits à coque")
filtrer_lactose = st.checkbox("Sans lactose")
filtrer_gluten = st.checkbox("Sans gluten")
filtrer_dop = st.checkbox("Certification anti-dopage")
filtrer_prix = st.checkbox("Le moins cher (1 élément par typologie de produit)")
filtrer_prix2 = st.checkbox("Les moins chers  (2 éléments par typologie de produit)")
filtrer_densite = st.checkbox("Densité énergétique maximale")
criteres_selectionnes = []
if filtrer_bio:
    criteres_selectionnes.append("Produits Bio")
if filtrer_noix:
    criteres_selectionnes.append("Sans fruits à coque")
if filtrer_lactose:
    criteres_selectionnes.append("Sans lactose")
if filtrer_gluten:
    criteres_selectionnes.append("Sans gluten")
if filtrer_dop:
    criteres_selectionnes.append("Certification anti-dopage")
if filtrer_prix:
    criteres_selectionnes.append("Le moins cher")
if filtrer_prix2:
    criteres_selectionnes.append("Les moins chers")
if filtrer_densite:
    criteres_selectionnes.append("Densité énergétique maximale")
proposition.append(f"--> Tu veux utiliser les marques suivantes: {', '.join(selection)} avec les critères suivants:{', '.join(criteres_selectionnes)}.")
if "Baouw" in marques:
    proposition.append(f"--> Obtiens 15% de réduction sur tout le site Baouw avec le code RUNBOOSTER15 via le lien suivant: https://www.baouw-organic-nutrition.com/?utm_source=affiliation&utm_medium=runbooster&utm_campaign=runbooster ")
# Filtrage par marque
if selection:
    df_filtre = df[df["Marque"].isin(selection)]
    # Vérifie s'il y a des produits de Ref "B"
    if objectif=="Finisher":
         df_suppl = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))]
         df_filtre = pd.concat([df_filtre, df_suppl], ignore_index=True)
    elif df_filtre[df_filtre["Ref"] == "B"].empty:
        # Ajoute les produits avec Marque == "Non communiquée"
        df_suppl = df[(df["Marque"] == "Non communiquée") & (df["Nom"] == "Sirop pur sucre")]
        df_filtre = pd.concat([df_filtre, df_suppl], ignore_index=True)
    df = df_filtre

#Filtrage caféine
if cafeine==0:
     df = df[df["Caf"] == 0]
# Appliquer les filtres booléens (Bio, Noix, Lactose, Gluten, DOP)
for critere in ["bio", "dop"]:
    if locals()[f"filtrer_{critere}"]:  # Vérifier si la checkbox est cochée
        df = df[df[critere] == 1]  # Garder uniquement les produits où la valeur est 1
for critere in ["noix", "lactose", "gluten"]:
    if locals()[f"filtrer_{critere}"]:  # Vérifier si la checkbox est cochée
        df = df[df[critere] == 0]  # Garder uniquement les produits où la valeur est 0

# Filtrer par Prix (2 moins chers par Ref)
if filtrer_prix and not filtrer_densite:
    df = df.sort_values(["Ref", "prix"]).groupby("Ref").head(1)
if filtrer_prix2 and not filtrer_densite:
    df = df.sort_values(["Ref", "prix"]).groupby("Ref").head(2)
# Filtrer par Densité (2 plus denses par Ref)
if filtrer_densite and not (filtrer_prix or filtrer_prix2):
    df = df.sort_values(["Ref", "densite"], ascending=False).groupby("Ref").head(1)
if (filtrer_densite & (filtrer_prix | filtrer_prix2)):
     df_prixdensite = df.sort_values(["Ref", "prix"]).groupby("Ref").head(4)
     df = df_prixdensite.sort_values(["Ref", "densite"], ascending=False).groupby("Ref").head(1)


st.divider()
filtrer_produits = st.checkbox("Critères avancés")
if filtrer_produits:
    # Crée une colonne de labels combinés pour affichage
    df["label"] = df["Marque"] + " - " + df["Nom"]
    # Multiselect avec Marque + Nom
    selected_labels = st.multiselect(
        "Sélectionne tes produits préférés, avec au MINIMUM une Boisson et une Compote ou Barre:",
        options=df["label"])
    # Filtrage du DataFrame d'origine via les labels
    df_selectionproduits = df[df["label"].isin(selected_labels)]
    if objectif=="Finisher":
         boissonfinisher = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))]
         df = pd.concat([boissonfinisher, df_selectionproduits])
    elif df_selectionproduits[df_selectionproduits["Ref"] == "B"].empty:
        # Ajoute les produits avec Marque == "Non communiquée"
         boissonfinisher = df[(df["Marque"] == "Non communiquée") & (df["Nom"] == "Sirop pur sucre")]
         df = pd.concat([boissonfinisher, df_selectionproduits])
    else:
         df=df_selectionproduits
# Affichage des résultats
st.write("### Produits sélectionnés :")
st.dataframe(df[["Ref", "Marque", "Nom", "prix", "Glucide", "densite"]].rename(columns={
        "prix": "Prix d'1g de glucide",
        "Glucide": "Glucides (g)",
        "densite": "Densité (glucide dans 1g de produit)",
    }))
     
st.divider()


refsel = ["BS", "BAS", "CS"]
df_prodsel = df[df["Ref"].isin(refsel)]
filtre_prodsel=df_prodsel.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(1, len(x))))
if cas in [1, 2, 4, 6]: #On filtre 2 produits de chaque Ref pour que ça ne soit pas le bazar
    refs = ["B", "BA", "C", "G"]
    df_ref = df[(df["Ref"].isin(refs)) & (df["Caf"] == 0)]
    prodreduits = df_ref.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(2, len(x))))
    df_caf = df[(df["Ref"].isin(["G", "BA"])) & (df["Caf"] > 20) & (df["Caf"] <= 101)]
    prodcaf = df_caf.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(1, len(x))))
    df = pd.concat([prodcaf, prodreduits])
if cas==3: 
    df = df[df["Caf"] == 0]
    refs = ["BA", "C"]
    df_sel12h = df[df["Ref"].isin(refs)]
    boissonfinisher = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))]
    barreetcompote = df_sel12h.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(2, len(x))))
    df = pd.concat([boissonfinisher, barreetcompote, filtre_prodsel])
if cas==5: 
    df = df[df["Caf"] == 0]
    refs = ["B", "BA", "C"]
    df_sel12h = df[df["Ref"].isin(refs)]
    filtre_cas5 = df_sel12h.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(2, len(x))))
    df = pd.concat([filtre_cas5, filtre_prodsel])
if cas==7:
    refs = ["B", "C", "G"]
    df_ref = df[(df["Ref"].isin(refs)) & (df["Caf"] == 0)]
    prodreduits = df_ref.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(2, len(x))))
    df_barre = df[(df["Ref"].isin(["BA"])) & (df["Caf"] == 0)]
    barrereduit = df_barre.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(1, len(x))))
    df_caf = df[(df["Ref"].isin(["G", "BA"])) & (df["Caf"] > 1) & (df["Caf"] <= 101)]
    prodcaf = df_caf.groupby("Ref", group_keys=False).apply(lambda x: x.sample(n=min(1, len(x))))
    df = pd.concat([prodcaf, prodreduits, filtre_prodsel, barrereduit])



st.subheader("Proposition d'un plan nutritionnel:", divider="red")
plan = []
def ajuster_x(glucide, min_cible, max_cible):
    if glucide > 1:  # Produit en sachet
        if min_cible <= glucide <= max_cible:  # Vérifie si 1 sachet est dans la cible
            return 1, "sachet"
        elif min_cible <= 0.5 * glucide <= max_cible:  # Vérifie si 0.5 sachet fonctionne
            return 0.5, "sachet"
        else:
            return 1, "sachet"  # Si rien ne marche, prendre un sachet entier (mieux vaut trop que pas assez)
    else:  # Produit en vrac
        x = round(max_cible / glucide)  # Calcule le nombre de grammes nécessaires pour être proche du max
        return x, "g"

if cas == 1:
    st.write("Pas de plan, se référer aux conseils ci-dessus.")

elif cas == 2:
    produit_B = df[df["Ref"] == "B"].sample(1).iloc[0]
    glucide = produit_B["Glucide"]
    x, unite = ajuster_x(glucide, Chotot-5, Chotot+5)  # Ajuste x et récupère l'unité
    if unite == "sachet":
         x_brut = Chotot / glucide
         valeurs_possibles = [0.5, 1, 2, 3]
         x = min(valeurs_possibles, key=lambda x: abs(x - x_brut))
    plan.append(f"Consommer {x} {unite} de {produit_B['Nom']} de marque {produit_B['Marque']} avec {eau}mL d’eau.")


elif cas in [3, 4, 5, 6, 7]:
    heures_pleines = int(tpsestimeh)
    derniere_heure = tpsestimeh % 1
    produit_1 = None
    hcaf=0
    hsel=4
    for heure in np.arange(0, heures_pleines, 1):
        if heure % 2 == 0 or produit_1 is None:
            if cas == 3:
                 produit_1 = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 15, int(random.uniform(15, 25)))
            elif cas == 4 or cas == 6:
                 produit_1 = df[(df["Caf"] == 0) & (df["Ref"] == "B")].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 30, int(random.uniform(30, 45)))
            elif cas == 5: 
                 if hsel==heure:
                      hsel+=5
                      produit_1 = df[df["Ref"].isin(["B", "BS"])].sample(1).iloc[0]
                 else:
                      produit_1 = df[df["Ref"].isin(["B"])].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 25, int(random.uniform(25, 30)))
            elif cas==7 and hsel==heure:
                 hsel+=5
                 produit_1 = df[(df["Caf"] == 0) & (df["Ref"].isin(["B", "BS"]))].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 30, int(random.uniform(30, 40)))
            else:
                 produit_1 = df[(df["Caf"] == 0) & (df["Ref"].isin(["B"]))].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 30, int(random.uniform(30, 45)))


        glucide_restant = Cho - (x_1 * glucide_1)
        if cas == 3 or cas == 5:
             if heure > 4 and heure % 2 != 0: #on met du salé toutes les heures impaires
                  produits_filtrés = df[(df["Ref"].isin(["C", "CS", "BA", "BAS"])) & (df["Glucide"] < glucide_restant+10)]
             else:
                  produits_filtrés = df[(df["Ref"].isin(["C", "BA"])) & (df["Glucide"] < glucide_restant+10)]
             
        elif cas == 4:
            if heure == 0:
                produits_filtrés = df[(df["Ref"].isin(["G", "C"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] > 20) & (df["Caf"] <= 101)]
                if produits_filtrés["Ref"].isin(["G", "C"]).sum() == 0:  # Vérifie si produits caféinés sont absents
                      produits_filtrés = df[(df["Ref"].isin(["G", "C"])) & (df["Glucide"] < glucide_restant+10)]
                      if produits_filtrés["Ref"].isin(["G", "C"]).sum() == 0:  # Vérifie si gels et compotes sont absents
                           produits_filtrés = df[(df["Ref"].isin(["BA"])) & (df["Glucide"] < glucide_restant+10)]
            else:
                 produits_filtrés = df[(df["Ref"].isin(["G", "C"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] == 0)]
                 if produits_filtrés["Ref"].isin(["G", "C"]).sum() == 0:  # Vérifie si gels et compotes sont absents
                      produits_filtrés = df[(df["Ref"].isin(["BA"])) & (df["Glucide"] < glucide_restant+10)]

        elif cas == 6:
            hcaf=int(tpsestimeh)-1
            if heure == 0 or heure == hcaf:
                 produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] > 20) & (df["Caf"] <= 101)]
                 if produits_filtrés["Ref"].isin(["G", "C", "BA"]).sum() == 0:  # Vérifie si produits caféinés sont absents
                      produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10)]
            else:
                 produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] == 0)]

        elif cas == 7 and heure > 4 and heure % 2 != 0: #on met du salé toutes les heures impaires
            produits_filtrés = df[(df["Ref"].isin(["G", "CS", "BAS"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] == 0)]
            if produits_filtrés["Ref"].isin(["CS", "BAS"]).sum() == 0:  # Vérifie si produits salés sont absents
                produits_supplémentaires = df[(df["Ref"].isin(["BA", "C"])) & (df["Glucide"] < glucide_restant + 10) & (df["Caf"] == 0)]
                produits_filtrés = pd.concat([produits_filtrés, produits_supplémentaires])
        elif cas == 7 and heure == hcaf:
            produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] > 1) & (df["Caf"] <= 101)]
            hcaf=hcaf+4
            if produits_filtrés["Ref"].isin(["G", "C", "BA"]).sum() == 0:  # Vérifie si produits caféinés sont absents
                produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10)]
        else:
            produits_filtrés = df[(df["Ref"].isin(["G", "C", "BA"])) & (df["Glucide"] < glucide_restant+10) & (df["Caf"] == 0)]


        if len(produits_filtrés) >= 2:
             produits_suivants = produits_filtrés.sample(2)
        else:
             produits_suivants = produits_filtrés  # Si moins de 2 produits, on prend tout ce qui est dispo
        
        produits_text = []
        glucide_tot=0
        sodium_tot=0
        caf_tot=0
        for produit in produits_suivants.itertuples():
            if glucide_restant <= 0:
                break
            if produit.Glucide <= glucide_restant+10:
                produits_text.append(f"+ 1 {produit.Nom} de la marque {produit.Marque}")
                glucide_restant -= produit.Glucide
                glucide_tot+=produit.Glucide
                sodium_tot+=produit.Sodium
                caf_tot+=produit.Caf
            
        if unite == "g":
             glucide_restant = Cho - glucide_tot
             x_1 = round(glucide_restant / glucide_1, 0)
        else:
             x_brut = (Cho - glucide_tot) / glucide_1
             valeurs_possibles = [0.5, 1, 2, 3]
             x_1 = min(valeurs_possibles, key=lambda x: abs(x - x_brut))
        glucide_tot+=produit_1.Glucide*x_1
        sodium_tot+=produit_1.Sodium*x_1
        caf_tot+=produit_1.Caf*x_1
        plan.append(f"🕐 Heure {heure} (Glucides: {int(glucide_tot)}g, Sodium: {int(sodium_tot*1000)}mg, Caféine: {int(caf_tot)}mg): {x_1} {unite} dans {eau}mL d'eau de {produit_1['Nom']} de la marque {produit_1['Marque']}  {', '.join(produits_text)}.")

    if derniere_heure > 0:
        eau=derniere_heure*eau
        glucide_tot=0
        sodium_tot=0
        caf_tot=0
        if cas == 3:
            produit_1 = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))].sample(1).iloc[0]
        else:
            produit_1 = df[df["Ref"] == "B"].sample(1).iloc[0]
        glucide_1 = produit_1["Glucide"]
        x_1, unite = ajuster_x(glucide_1, 30 * derniere_heure, 40 * derniere_heure)
        glucide_tot+=produit_1.Glucide*x_1
        sodium_tot+=produit_1.Sodium*x_1
        caf_tot+=produit_1.Caf*x_1

        glucide_restant = (Cho * derniere_heure) - (x_1 * glucide_1)
        if cas == 3 or cas == 5:
            produits_suivants = df[(df["Ref"].isin(["C", "CS", "BA", "BAS"]))].sample(1)
        elif cas == 4:
             produits_suivants = df[(df["Ref"].isin(["G", "C"]))]
             if produits_suivants["Ref"].isin(["G", "C"]).sum() == 0:  # Vérifie si gels et compotes sont absents
                  produits_suivants = df[(df["Ref"].isin(["BA"]))].sample(1)
             else:
                  produits_suivants = df[(df["Ref"].isin(["G", "C"]))].sample(1)
             
        elif cas == 6:
            produits_suivants = df[(df["Ref"].isin(["G", "C", "BA"]))].sample(1)
        else:
            produits_suivants = df[(df["Ref"].isin(["G", "C", "CS", "BA", "BAS"]))].sample(1)

        produits_text = []
        for produit in produits_suivants.itertuples():
            if glucide_restant <= 0:
                break
            if produit.Glucide <= glucide_restant:
                produits_text.append(f"+ 1 {produit.Nom} de la marque {produit.Marque}")
                glucide_restant -= produit.Glucide
                glucide_tot+=produit.Glucide
                sodium_tot+=produit.Sodium*1000
                caf_tot+=produit.Caf
        
        plan.append(f"🕐 Dernière heure (Glucides: {int(glucide_tot)}g, Sodium: {int(sodium_tot)}mg, Caféine: {int(caf_tot)}mg) : {x_1} {unite} dans {int(eau)}mL d'eau de {produit_1['Nom']} de la marque {produit_1['Marque']}  {', '.join(produits_text)}.")


     

    # Conseils ajoutés
conseils = [
        "+Pour la boisson, tu peux regrouper la quantité de deux heures dans une seule gourde, la 2e gourde étant",
        "consacrée à l'eau pour se rincer la bouche.",
        "+Tu peux commencer par augmenter ta quantité de glucides ingérée les 3 jours avant la course, pour faire",
        "tes stocks de glycogène musculaire (énergie), en mangeant un peu plus de féculents (riz, pâtes, patates, pain,…),",
        "et en réduisant les fibres (légumes crus, céréales complètes, légumineuses,…) ainsi que les graisses.",
        "Ton dernier repas avant la course doit être pris au moins 3h avant le départ, et être assez léger,",
        "ce n’est plus le moment de se surcharger le ventre.",
        "   ",
        "+Hydrate toi dès les premières minutes de course.",
        "+Evite les graisses saturées au ravitaillement (fromage, charcuterie,...), ils n'ont pas d'intérêt et",
        "alourdirons ton estomac.",
        "+En trail, évite les aliments solides à l'entame d'une descente et prends plutôt un aliment liquide.",
        "Privilégie les aliments solides en fin de descente ou début de montée pour ne pas avoir de troubles digestifs.",
        "Se réserver le droit de prendre un gel caféiné en cas de coup de mou.",
        "ATTENTION :",
        "++Ne dépasse pas 400mg de caféine dans la journée.",
        "++Boire plus de 800mL d'eau par heure peut être dangereux.",
        "++Pour les allergies, notre comparatif doit être revérifié, ne prenez pas nos informations à la lettre.",
        "+Si plus de 70g de glucides sont consommés par heure, entraîne ton intestin à l'entraînement (Gut training).",
        "+Teste les différents produits avant le jour J.",
        "+La consultation d'un professionnel de santé est conseillée en cas de doute."
]



def generer_pdf(contenu):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=14)

    # Titre du PDF
    pdf.cell(200, 10, "Résumé de ton Plan Nutritionnel", ln=True, align='C')
    pdf.ln(10)

    # Ajout du contenu en forçant l'encodage UTF-8
    pdf.set_font("Arial", size=11)
    for ligne in proposition:
        pdf.multi_cell(0, 10, ligne.encode("latin-1", "ignore").decode("latin-1"))
    pdf.set_font("Arial", size=14)
    for ligne in plan:
        if ligne:
            try:
                pdf.multi_cell(0, 10, ligne.encode("latin-1", "ignore").decode("latin-1"))
            except Exception as e:
                print(f"Erreur d'encodage : {e}, ligne ignorée: {ligne}")
         # Séparation
    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, "Conseils nutrition & sécurité", ln=True)
    pdf.set_font("Arial", size=11)
    for conseil in conseils:
        pdf.multi_cell(0, 8, conseil.encode("latin-1", "ignore").decode("latin-1"))

    # Sauvegarde du PDF
    pdf_filename = "plan_nutritionnel.pdf"
    pdf.output(pdf_filename)
    return pdf_filename

# === Fonction d'envoi d'email ===
def envoyer_email(destinataire, fichier_pdf):
    expediteur = "plan.runbooster@gmail.com"
    mot_de_passe = "zxkt evcb usww bgyt"  # Utiliser une variable d'environnement !

    msg = EmailMessage()
    msg["Subject"] = "Ton Plan Nutritionnel de course 📄"
    msg["From"] = expediteur
    msg["To"] = destinataire
    msg.set_content(f"Bonjour {nom},\n\nTu trouveras ci-joint ton plan nutritionnel en PDF pour ta course de {distance} kilomètres.\n\nBonne course!")

    # Ajouter le PDF en pièce jointe
    with open(fichier_pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=fichier_pdf)

    # Envoi via SMTP
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
            serveur.login(expediteur, mot_de_passe)
            serveur.send_message(msg)
        st.success(f"📧 Email envoyé avec succès à {destinataire} !")
    except Exception as e:
        st.error(f"❌ Erreur lors de l'envoi de l'email : {e}")


if not selection and not (filtrer_densite | filtrer_prix | filtrer_prix2) and tpsestimeh>=3:
     RecoMarque = [
          "Nous te conseillons de choisir une ou deux marques de nutrition pour ne pas que ton plan devienne un capharnaüm.",
          "Nos recommandations:",
          "+Baouw pour des produits bio et naturel, respectueux du corps et très gourmands.",
          "+Decathlon pour la simplicité d'accès à ses rayons et ses prix très abordables",
          "+Nduranz et 4Endurance pour leurs prix imbattables",
          "+Naak pour ses engagements", 
          "+Ergysport, Authentic Nutrition, CooknRun, Atlet Nutrition, Meltonic, Gourmiz pour leurs valeurs et leur origine."]
     st.markdown("\n".join([f"- {ligne.strip('+')}" if ligne.strip().startswith("+") else ligne for ligne in RecoMarque]))
          


nom = st.text_input("Prénom (facultatif)")
email = st.text_input("Votre adresse e-mail pour recevoir un récapitulatif et les actus RunBooster en cliquant sur le bouton 'Recevoir' (facultatif)")

if st.button("Créer mon Plan Nutritionnel"):
# Affichage du plan nutritionnel
    if plan:
         st.write("### Plan nutritionnel généré :")
         for ligne in proposition:
              st.write(ligne)
         for ligne in plan:
              st.write(ligne)
              
         st.markdown("### Conseils nutritionnels 🥤🍌\n")
         st.markdown("\n".join([f"- {ligne.strip('+')}" if ligne.strip().startswith("+") else ligne for ligne in conseils]))



if st.button("Recevoir mon Plan par Email"):
     if email:
          if plan:  # Vérification que le plan n'est pas vide
               contenu_plan = [str(l) for l in plan if l]  # Nettoyer les valeurs nulles

                 # Générer le PDF
               fichier_pdf = generer_pdf(contenu_plan)

                 # Envoyer l'email
               envoyer_email(email, fichier_pdf)

                 # Supprimer le fichier après envoi
               os.remove(fichier_pdf)
          else:
               st.warning("❌ Aucun plan nutritionnel généré.")
     else:
          st.warning("❌ Veuillez entrer une adresse email valide.")
