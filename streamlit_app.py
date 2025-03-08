import streamlit as st
import pandas as pd
import random
import smtplib
import numpy as np
from email.mime.text import MIMEText

produits = "produits.xlsx"  
df = pd.read_excel(produits, sheet_name="Produits énergétiques", engine="openpyxl")

left, middle =st.columns([1,3], vertical_alignment="bottom")
left.image("RunBooster(1).png", width=100) 
middle.subheader("Boost ton run grâce à une alimentation controlée")
st.divider()

discipline = st.radio("Choisi ta discipline 👇", ["Trail", "Course sur route / Vélo"], horizontal=True)
distance = st.number_input("Entre la distance de ta course en km", format="%0.1f")

if discipline=="Trail":
     cote = st.number_input("Entre ta cote ITRA ou UTMB Index", min_value=1, value=500)
     deniv = st.number_input("Entre le dénivelé positif en m", format="%0f")
     disteff=(distance+(deniv/100))
     tpsestime=1000*(0.00000006964734390393*(disteff)*(disteff)*(disteff)*(disteff)-0.00006550491191697*(disteff)*(disteff)*(disteff)+0.020181800970007*(disteff)*(disteff)+2.20983621768921*(disteff))/cote
else:
     st.write("Entre ton temps de course estimé 👇")
     tpsh=st.number_input("Heures", min_value=0)
     tpsm=st.number_input("Minutes", min_value=0, max_value=59)
     tpsestime=(tpsh*60)+tpsm
tpsestimeh=tpsestime/60
st.write('➜Temps de course estimé:', int(tpsestime), 'minutes, soit', int(tpsestimeh), 'h', int((tpsestimeh%1)*60), 'min' )


objectif=st.radio("Choisi ton objectif 👇", ["Performance", "Plaisir", "Finisher"], horizontal=True)
temp=st.checkbox("Cocher si plus de 20°C annoncés")
st.divider()
if objectif=="Performance" and tpsestimeh<1:
        cas=1
        Cho=0
        st.write("Tu consommeras un peu de boisson d'effort à l'échauffement, et un petit gel 5min avant le départ.")
elif objectif!="Performance" and tpsestimeh<1:
        cas=1
        Cho=0
        st.write('Tu consommeras une compote sucrée 5min avant le départ.')
elif (objectif=="Performance" or objectif=="Plaisir") and 1<=tpsestimeh<2:
        Cho=45
        cas=2
elif objectif=="Performance" and 2<=tpsestimeh<3:
        Cho=70
        cas=4
elif objectif=="Performance" and 3>=tpsestimeh>5:
        Cho=80
        cas=6
elif objectif=="Performance" and tpsestimeh>=5:
        Cho=80
        cas=7
elif objectif=="Plaisir" and tpsestimeh>=2:
        Cho=60
        cas=5
        
else:
        cas=3
        Cho=40

Chotot=Cho*tpsestimeh
st.write('➜Tu consommeras', Cho,'g de glucides par heure, soit', int(Chotot), 'grammes de glucides sur la course')

if temp and tpsestimeh>=2:
        st.write('➜Tu ajouteras dans ta gourde, 1g de sel de table par heure de course, pour compenser tes pertes en sodium')
if objectif=="Performance" and tpsestimeh>=5:
        st.write('➜Tu ajouteras dans ta gourde, 3g de BCAA 2.1.1 par heure de course, pour limiter les fatigues musculaire et nerveuse')
if tpsestimeh>=3:
        st.write("➜Evite les graisses saturées au ravitaillement (fromage, charcuterie,...), ils n'ont pas d'intérêt et alourdirons ton estomac")
        
st.divider()


def load_data():
    df = pd.read_excel("produits.xlsx")  # Remplace par ton fichier
    df["Marque"] = df["Marque"].astype(str)  # Convertir toutes les valeurs en string
    return df

df = load_data()

# Liste des marques uniques avec "Aucune" en option
marques = ["Aucune"] + sorted(df["Marque"].dropna().unique().tolist(), key=str)
# Sélection multiple des marques
selection = st.multiselect("Quelles sont tes marques de nutrition préférées? 👇", marques, default=["Aucune"])
st.write("Choisi 'Aucune' si tu veux laisser RunBooster choisir pour toi. Sinon, décoche le." )

st.write("As-tu des critères? 👇")
filtrer_bio = st.checkbox("Produits Bio")
filtrer_noix = st.checkbox("Sans fruits à coque")
filtrer_lactose = st.checkbox("Sans lactose")
filtrer_gluten = st.checkbox("Sans gluten")
filtrer_dop = st.checkbox("Certification anti-dopage")
filtrer_prix = st.checkbox("Le moins cher")
filtrer_densite = st.checkbox("Densité énergétique maximale")

# Filtrage par marque
if "Aucune" not in selection:
    df = df[df["Marque"].isin(selection) | (df["Marque"] == "Non communiquée")]

# Appliquer les filtres booléens (Bio, Noix, Lactose, Gluten, DOP)
for critere in ["bio", "dop"]:
    if locals()[f"filtrer_{critere}"]:  # Vérifier si la checkbox est cochée
        df = df[df[critere] == 1]  # Garder uniquement les produits où la valeur est 1
for critere in ["noix", "lactose", "gluten"]:
    if locals()[f"filtrer_{critere}"]:  # Vérifier si la checkbox est cochée
        df = df[df[critere] == 0]  # Garder uniquement les produits où la valeur est 0

# Filtrer par Prix (2 moins chers par Ref)
if filtrer_prix:
    df = df.sort_values(["Ref", "prix"]).groupby("Ref").head(3)

# Filtrer par Densité (2 plus denses par Ref)
if filtrer_densite:
    df = df.sort_values(["Ref", "densite"], ascending=False).groupby("Ref").head(3)

# Affichage des résultats
st.write("### Produits trouvés :")
st.dataframe(df[["Ref", "Marque", "Nom", "prix", "densite"] + ["bio", "noix", "lactose", "gluten", "dop"]])


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
    plan.append(f"Consommer {x} {unite} de {produit_B['Nom']} de marque {produit_B['Marque']} dans 500mL d’eau.")


elif cas in [3, 4]:
    heures_pleines = int(tpsestimeh)
    derniere_heure = tpsestimeh % 1
    produit_1 = None
    for heure in np.arange(0, heures_pleines, 1):
        if heure % 2 == 0 or produit_1 is None:
            if cas == 3:
                 produit_1 = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 15, int(random.uniform(15, 25)))
            else:
                 produit_1 = df[df["Ref"] == "B"].sample(1).iloc[0]
                 glucide_1 = produit_1["Glucide"]
                 x_1, unite = ajuster_x(glucide_1, 30, int(random.uniform(30, 45)))

        glucide_restant = Cho - (x_1 * glucide_1)
        produits_filtrés = df[(df["Ref"].isin(["G", "C", "CS", "BA", "BAS"])) & (df["Glucide"] < glucide_restant+10)]
        if len(produits_filtrés) >= 2:
             produits_suivants = produits_filtrés.sample(2)
        else:
             produits_suivants = produits_filtrés  # Si moins de 2 produits, on prend tout ce qui est dispo
        
        produits_text = []
        for produit in produits_suivants.itertuples():
            if glucide_restant <= 0:
                break
            if produit.Glucide <= glucide_restant+8:
                produits_text.append(f"+ 1 {produit.Nom} de la marque {produit.Marque}")
                glucide_restant -= produit.Glucide
        
        plan.append(f"🕐 Heure {heure}: {x_1} {unite} de {produit_1['Nom']} de la marque {produit_1['Marque']}  {', '.join(produits_text)}.")

    if derniere_heure > 0:
        if cas == 3:
            produit_1 = df[df["Nom"].fillna("").str.startswith(("Jus", "Sirop"))].sample(1).iloc[0]
        else:
            produit_1 = df[df["Ref"] == "B"].sample(1).iloc[0]
        glucide_1 = produit_1["Glucide"]
        x_1, unite = ajuster_x(glucide_1, 30 * derniere_heure, 40 * derniere_heure)

        glucide_restant = (Cho * derniere_heure) - (x_1 * glucide_1)
        produits_suivants = df[df["Ref"].isin(["G", "C", "BA", "BAS", "CS"])].sample(2)
        produits_text = []
        for produit in produits_suivants.itertuples():
            if glucide_restant <= 0:
                break
            if produit.Glucide <= glucide_restant:
                produits_text.append(f"+ 1 {produit.Nom} de la marque {produit.Marque}")
                glucide_restant -= produit.Glucide
        
        plan.append(f"🕐 Heure {int(tpsestimeh)} (dernière heure) : {x_1}g de {produit_1['Nom']} de la marque {produit_1['Marque']}  {', '.join(produits_text)}.")

if st.button("Créer mon Plan Nutritionnel"):
    st.write("Allons-y")
# Affichage du plan nutritionnel
    if plan:
         st.write("### Plan nutritionnel généré :")
         for ligne in plan:
              st.write(ligne)
         st.write("Conseil: regrouper la quantité de deux heures dans une seule gourde, la 2e gourde étant consacrée à l'eau pour se rincer la bouche")










st.divider()
nom = st.text_input("Prénom")
email = st.text_input("Votre adresse e-mail pour recevoir un récapitulatif")
if st.button("Envoyer un récapitulatif par e-mail"):
    if email:
        # Construire le message
        message = f"""
        Bonjour {nom},

        Voici un résumé des informations que vous avez saisies :

        - Nom : {nom}

        Merci d'avoir utilisé notre service !

        Cordialement,
        L'équipe RunBooster
        """

        # Configuration de l'envoi d'e-mail (remplacez par vos propres identifiants SMTP)
        sender_email = "baptiste.runbooster@gmail.com"
        sender_password = "votre_mot_de_passe"
        recipient_email = email

        msg = MIMEText(message)
        msg["Subject"] = "Votre plan nutritionnel"
        msg["From"] = sender_email
        msg["To"] = recipient_email

        try:
            # Connexion au serveur SMTP
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()

            st.success("E-mail envoyé avec succès !")
        except Exception as e:
            st.error(f"Erreur lors de l'envoi de l'e-mail : {e}")
    else:
        st.warning("Veuillez entrer une adresse e-mail valide.")
#Un e-mail lui est envoyé via SMTP (Gmail dans cet exemple), 
#Vous devez activer "Accès aux applications moins sécurisées" sur votre compte Gmail pour envoyer des e-mails via SMTP, 
#Pour éviter d'exposer vos identifiants, utilisez des variables d'environnement ou un service tiers comme SendGrid.
