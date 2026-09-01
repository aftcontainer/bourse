import os
from io import BytesIO
from django.db import transaction
from django.db.models import Count, Sum, Q
from reportlab.lib.enums import TA_CENTER,TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle, HRFlowable,
)
from reportlab.pdfgen import canvas
from datetime import datetime, date

from mainapp.models import IndexTitre, Titre, Portefeuille, Operation

from django.conf import settings

from mainapp.utils import generer_numero_certificat

LOGO_PATH = os.path.join(settings.BASE_DIR, "static", "mainapp/logos", "logo_AFG_Bank.png")

from reportlab.lib.units import cm

from num2words import num2words


class GestionIndexTitre:

    @staticmethod
    def vendre(vendeur, acheteur, titre, quantite):

        plages = (
            IndexTitre.objects
            .select_for_update()
            .filter(
                client=vendeur,
                titre=titre,
                statut_tire=1
            )
            .order_by("debut_index")
        )

        restant = quantite

        nouvelles_plages = []

        with transaction.atomic():

            for plage in plages:

                if restant == 0:
                    break

                taille = plage.fin_index - plage.debut_index + 1

                # toute la plage est vendue
                if taille <= restant:

                    nouvelles_plages.append(
                        IndexTitre(
                            client=acheteur,
                            etablissement=plage.etablissement,
                            titre=titre,
                            debut_index=plage.debut_index,
                            fin_index=plage.fin_index,
                            statut_tire=1,
                            indordre=plage.indordre
                        )
                    )

                    restant -= taille

                    plage.delete()

                # découpage
                else:

                    debut_transfert = plage.debut_index
                    fin_transfert = plage.debut_index + restant - 1

                    nouvelles_plages.append(
                        IndexTitre(
                            client=acheteur,
                            etablissement=plage.etablissement,
                            titre=titre,
                            debut_index=debut_transfert,
                            fin_index=fin_transfert,
                            statut_tire=1,
                            indordre=plage.indordre
                        )
                    )

                    plage.debut_index = fin_transfert + 1
                    plage.save(update_fields=["debut_index"])

                    restant = 0

            if restant > 0:
                raise ValueError("Le vendeur ne possède pas suffisamment de titres.")

            IndexTitre.objects.bulk_create(nouvelles_plages)

            GestionIndexTitre.fusionner(acheteur, titre)
            GestionIndexTitre.fusionner(vendeur, titre)

    @staticmethod
    def fusionner(client, titre):

        plages = list(
            IndexTitre.objects.filter(
                client=client,
                titre=titre
            ).order_by("debut_index")
        )

        if len(plages) < 2:
            return

        precedente = plages[0]

        for plage in plages[1:]:

            if precedente.fin_index + 1 == plage.debut_index:

                precedente.fin_index = plage.fin_index
                precedente.save(update_fields=["fin_index"])

                plage.delete()

            else:
                precedente = plage


def nombre_en_lettres(n):
    if n == 0:
        return "zéro"

    unites = [
        "", "un", "deux", "trois", "quatre",
        "cinq", "six", "sept", "huit", "neuf"
    ]

    dizaines = [
        "", "", "vingt", "trente", "quarante",
        "cinquante", "soixante", "soixante-dix",
        "quatre-vingt", "quatre-vingt-dix"
    ]


    def moins_de_mille(n):

        if n < 10:
            return unites[n]


        if n < 20:
            return [
                "dix",
                "onze",
                "douze",
                "treize",
                "quatorze",
                "quinze",
                "seize",
                "dix-sept",
                "dix-huit",
                "dix-neuf"
            ][n - 10]


        if n < 100:

            dizaine = n // 10
            reste = n % 10

            if dizaine == 7:
                return "soixante-" + moins_de_mille(10 + reste)

            if dizaine == 9:
                return "quatre-vingt-" + moins_de_mille(10 + reste)

            if reste == 0:

                if dizaine == 8:
                    return "quatre-vingts"

                return dizaines[dizaine]


            if reste == 1 and dizaine not in [8]:
                return dizaines[dizaine] + " et un"


            return dizaines[dizaine] + "-" + unites[reste]


        centaine = n // 100
        reste = n % 100


        if centaine == 1:
            texte = "cent"
        else:
            texte = unites[centaine] + " cent"


        if reste == 0 and centaine > 1:
            texte += "s"


        if reste:
            texte += " " + moins_de_mille(reste)


        return texte

    if n < 1000:
        return moins_de_mille(n)

    if n < 1_000_000:

        mille = n // 1000
        reste = n % 1000

        if mille == 1:
            texte = "mille"
        else:
            texte = moins_de_mille(mille) + " mille"


        if reste:
            texte += " " + moins_de_mille(reste)


        return texte



    if n < 1_000_000_000:

        million = n // 1_000_000
        reste = n % 1_000_000


        texte = moins_de_mille(million)

        if million > 1:
            texte += " millions"
        else:
            texte += " million"


        if reste:
            texte += " " + nombre_en_lettres(reste)


        return texte


    return str(n)

def formater_nombre(n):
    """Formate un entier avec espace comme séparateur de milliers (ex: 2 388)."""
    return f"{n:,}".replace(",", " ")

def formater_pourcentage(p):
    """Formate un pourcentage avec virgule française (ex: 94,70 %)."""
    return f"{p:.2f} %".replace(".", ",")

def construire_pdf_registre_central(public_id, buffer=None, logo_path=LOGO_PATH):
    titre = Titre.objects.get(public_id=public_id)
    nom_titre = titre.libelle

    # Regroupement des portefeuilles par établissement pour ce titre
    lignes = (
        Portefeuille.objects
        .filter(titre=titre)
        .values(f"etablissement__libelle")
        .annotate(
            nb_actionnaires=Count("client", distinct=True),
            nombre_titres=Sum("nb_titre"),
        )
        .order_by(f"etablissement__libelle")
    )

    total_titres = sum(l["nombre_titres"] or 0 for l in lignes)
    total_actionnaires = sum(l["nb_actionnaires"] or 0 for l in lignes)

    # --- Construction du document ---
    output = buffer if buffer is not None else BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    titre_style = ParagraphStyle(
        "TitreDoc", parent=styles["Title"], fontSize=14, alignment=TA_CENTER, leading=18,
    )
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=10)
    label_centre_style = ParagraphStyle(
        "LabelCentre", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER,
    )

    # En-tête : titre du document centré + logo optionnel à droite
    if logo_path:
        entete = Table(
            [[
                "",
                Paragraph("REGISTRE CENTRAL DES<br/>ACTIONS PAR AFFILIES", titre_style),
                Image(logo_path, width=3 * cm, height=1.8 * cm),
            ]],
            colWidths=[3 * cm, 11 * cm, 3 * cm],
        )
        entete.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(entete)
    else:
        story.append(Paragraph("REGISTRE CENTRAL DES ACTIONS PAR AFFILIES", titre_style))

    story.append(Spacer(1, 0.7 * cm))

    date_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    story.append(Paragraph(f"EN DATE DU :&nbsp;&nbsp;&nbsp;{date_str}", label_centre_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"VALEUR :&nbsp;&nbsp;<b>{nom_titre.upper()}</b>", label_style))
    story.append(Spacer(1, 0.5 * cm))

    # Tableau des résultats
    entetes = ["Etablissement", "Nb d'actionnaires", "Nombre de titres", "Pourcentage"]
    table_data = [entetes]

    for ligne in lignes:
        nb_titres_etab = ligne["nombre_titres"] or 0
        pourcentage = (nb_titres_etab / total_titres * 100) if total_titres else 0
        table_data.append([
            ligne[f"etablissement__libelle"],
            str(ligne["nb_actionnaires"]),
            formater_nombre(nb_titres_etab),
            formater_pourcentage(pourcentage),
        ])

    # Ligne de totaux (sans pourcentage, comme dans le modèle)
    table_data.append(["", str(total_actionnaires), formater_nombre(total_titres), ""])

    # Largeur totale disponible = largeur A4 (21cm) - marges gauche/droite (2cm + 2cm) = 17cm
    table = Table(table_data, colWidths=[6 * cm, 3.8 * cm, 4.2 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    doc.build(story)
    if buffer is None:
        output.seek(0)
    return output

# def generer_historique_mouvements_pdf(client, titre):
#     operations = (
#         Operation.objects
#         .filter(
#             Q(client=client) | Q(beneficiaire=client),
#             titre=titre,
#         )
#         .order_by("date_ordre")
#     )
#
#     lignes = []
#     solde = 0
#     total_credit = 0
#     total_debit = 0
#
#     for op in operations:
#         avant = solde
#         nb = op.nb_titre or 0
#
#         if op.sens == "C":
#             credit, debit = nb, None
#             solde += nb
#         else:  # op.sens == "D"
#             credit, debit = None, nb
#             solde -= nb
#
#         total_credit += credit or 0
#         total_debit += debit or 0
#
#         libelle = op.type_operation.libelle if op.type_operation_id else (op.code_op or "")
#
#         lignes.append([
#             op.date_ordre.strftime("%d/%m/%Y") if op.date_ordre else "",
#             libelle,
#             avant,
#             credit,
#             debit,
#             solde,
#         ])
#
#     nombre_actions_final = solde
#     valeur_nominale_unitaire = getattr(titre, "nominal", 0) or 0
#     valeur_nominale_totale = nombre_actions_final * valeur_nominale_unitaire
#
#     buffer = BytesIO()
#
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=A4,
#         topMargin=15 * mm,
#         bottomMargin=15 * mm,
#         leftMargin=15 * mm,
#         rightMargin=15 * mm,
#     )
#
#     styles = getSampleStyleSheet()
#     style_normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=9)
#     style_titre = ParagraphStyle(
#         "titre", parent=styles["Heading1"], alignment=TA_CENTER,
#         fontSize=13, spaceAfter=2,
#     )
#     style_soustitre = ParagraphStyle(
#         "soustitre", parent=styles["Normal"], alignment=TA_CENTER,
#         fontSize=10, fontName="Helvetica-Bold",
#     )
#     style_date_droite = ParagraphStyle("date_droite", parent=style_normal, alignment=TA_RIGHT)
#
#     story = []
#
#     # --- En-tête : logo gauche, titre centré, logo droite, date en haut à droite ---
#     date_str = f"Libreville, le {date.today().strftime('%d/%m/%Y')}"
#     story.append(Paragraph(date_str, style_date_droite))
#     story.append(Spacer(1, 4))
#
#     if os.path.exists(LOGO_PATH):
#         logo_gauche = Image(LOGO_PATH, width=28 * mm, height=14 * mm)
#         logo_droite = Image(LOGO_PATH, width=28 * mm, height=14 * mm)
#     else:
#         logo_gauche = Paragraph("", style_normal)
#         logo_droite = Paragraph("", style_normal)
#
#     titre_bloc = [
#         Paragraph("HISTORIQUE DES MOUVEMENTS", style_titre),
#         Paragraph(f"TITRE : {titre.libelle.upper()}", style_soustitre),
#     ]
#
#     entete_table = Table(
#         [[logo_gauche, titre_bloc, logo_droite]],
#         colWidths=[35 * mm, 110 * mm, 35 * mm],
#     )
#     entete_table.setStyle(TableStyle([
#         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
#         ("ALIGN", (0, 0), (0, 0), "LEFT"),
#         ("ALIGN", (2, 0), (2, 0), "RIGHT"),
#     ]))
#     story.append(entete_table)
#     story.append(Spacer(1, 10))
#
#     # --- Informations du titulaire ---
#     nom_complet = getattr(client, "nom_complet", None) or f"{client.nom_client} {client.prenom_client}".strip()
#     adresse = getattr(client, "adresse", "") or ""
#     telephone = getattr(client, "telephone", "") or ""
#
#     info_data = [
#         [Paragraph(f"Identifiant : <b>{client.indentifiant}</b>", style_normal), ""],
#         [Paragraph(f"Nom du titulaire : <b>{nom_complet.upper()}</b>", style_normal), ""],
#         [Paragraph(f"Adresse : {adresse}", style_normal),
#          Paragraph(f"Tél. : {telephone}", style_normal)],
#         [Paragraph(f"Nombre d'actions : <b>{formater_nombre(nombre_actions_final)}</b>", style_normal),
#          Paragraph(f"Valeur nominale : <b>{formater_nombre(valeur_nominale_totale)}</b>", style_normal)],
#     ]
#     info_table = Table(info_data, colWidths=[110 * mm, 70 * mm])
#     info_table.setStyle(TableStyle([
#         ("VALIGN", (0, 0), (-1, -1), "TOP"),
#         ("TOPPADDING", (0, 0), (-1, -1), 2),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
#     ]))
#     story.append(info_table)
#     story.append(Spacer(1, 10))
#
#     entetes = ["Date", "Libellé mouvement", "Nbre avant\ntransaction", "CREDIT", "DEBIT", "Nbre après\ntransaction"]
#     data = [entetes]
#     for date_str_ligne, libelle, avant, credit, debit, apres in lignes:
#         data.append([
#             date_str_ligne,
#             libelle,
#             avant,
#             credit,
#             debit,
#             apres,
#         ])
#     data.append(["", "TOTAL :", "", formater_nombre(total_credit), formater_nombre(total_debit), ""])
#
#     col_widths = [22 * mm, 55 * mm, 28 * mm, 20 * mm, 20 * mm, 28 * mm]
#     mouvements_table = Table(data, colWidths=col_widths, repeatRows=1)
#
#     style_commands = [
#         ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
#         ("FONTSIZE", (0, 0), (-1, -1), 8.5),
#         ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
#         ("ALIGN", (2, 0), (-1, -1), "CENTER"),
#         ("ALIGN", (0, 0), (1, -1), "LEFT"),
#         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
#         ("GRID", (0, 0), (-1, -2), 0.5, colors.black),
#         ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
#         ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
#         ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
#         ("SPAN", (0, -1), (1, -1)),  # fusionne Date + Libellé sur la ligne TOTAL
#         ("TOPPADDING", (0, 0), (-1, -1), 4),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
#     ]
#     mouvements_table.setStyle(TableStyle(style_commands))
#     story.append(mouvements_table)
#
#     doc.build(story)
#     buffer.seek(0)
#     return buffer.getvalue()

def generer_historique_mouvements_pdf(client, titre):
    operations = (
        Operation.objects
        .filter(
            Q(client=client) | Q(beneficiaire=client),
            titre=titre,
        )
        .order_by("date_ordre")
    )

    lignes = []
    solde = 0
    total_credit = 0
    total_debit = 0

    for op in operations:
        avant = solde
        nb = op.nb_titre or 0

        est_beneficiaire = (op.beneficiaire_id == client.pk)

        if est_beneficiaire:
            credit, debit = nb, None
            solde += nb
        else:
            credit, debit = None, nb
            if op.type_operation.libelle == "Souscription augmentation de capital" or op.type_operation.libelle == "Report des Actions":
                solde += nb
            else:
                solde -= nb

        total_credit += credit or 0
        total_debit += debit or 0

        libelle = op.type_operation.libelle if op.type_operation_id else (op.code_op or "")

        lignes.append([
            op.date_ordre.strftime("%d/%m/%Y") if op.date_ordre else "",
            libelle,
            avant,
            credit,
            debit,
            solde,
        ])

    nombre_actions_final = solde
    valeur_nominale_unitaire = getattr(titre, "nominal", 0) or 0
    valeur_nominale_totale = nombre_actions_final * valeur_nominale_unitaire

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=9)
    style_titre = ParagraphStyle(
        "titre", parent=styles["Heading1"], alignment=TA_CENTER,
        fontSize=13, spaceAfter=2,
    )
    style_soustitre = ParagraphStyle(
        "soustitre", parent=styles["Normal"], alignment=TA_CENTER,
        fontSize=10, fontName="Helvetica-Bold",
    )
    style_date_droite = ParagraphStyle("date_droite", parent=style_normal, alignment=TA_RIGHT)

    story = []

    # --- En-tête : logo gauche, titre centré, logo droite, date en haut à droite ---
    date_str = f"Libreville, le {date.today().strftime('%d/%m/%Y')}"
    story.append(Paragraph(date_str, style_date_droite))
    story.append(Spacer(1, 4))

    if os.path.exists(LOGO_PATH):
        logo_gauche = Image(LOGO_PATH, width=28 * mm, height=14 * mm)
        logo_droite = Image(LOGO_PATH, width=28 * mm, height=14 * mm)
    else:
        logo_gauche = Paragraph("", style_normal)
        logo_droite = Paragraph("", style_normal)

    titre_bloc = [
        Paragraph("HISTORIQUE DES MOUVEMENTS", style_titre),
        Paragraph(f"TITRE : {titre.libelle.upper()}", style_soustitre),
    ]

    entete_table = Table(
        [[logo_gauche, titre_bloc, logo_droite]],
        colWidths=[35 * mm, 110 * mm, 35 * mm],
    )
    entete_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(entete_table)
    story.append(Spacer(1, 10))

    # --- Informations du titulaire ---
    nom_complet = getattr(client, "nom_complet", None) or f"{client.nom_client} {client.prenom_client}".strip()
    adresse = getattr(client, "adresse", "") or ""
    telephone = getattr(client, "telephone", "") or ""

    info_data = [
        [Paragraph(f"Identifiant : <b>{client.indentifiant}</b>", style_normal), ""],
        [Paragraph(f"Nom du titulaire : <b>{nom_complet.upper()}</b>", style_normal), ""],
        [Paragraph(f"Adresse : {adresse}", style_normal),
         Paragraph(f"Tél. : {telephone}", style_normal)],
        [Paragraph(f"Nombre d'actions : <b>{formater_nombre(nombre_actions_final)}</b>", style_normal),
         Paragraph(f"Valeur nominale : <b>{formater_nombre(valeur_nominale_totale)}</b>", style_normal)],
    ]
    info_table = Table(info_data, colWidths=[110 * mm, 70 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    entetes = ["Date", "Libellé mouvement", "Nbre avant\ntransaction", "CREDIT", "DEBIT", "Nbre après\ntransaction"]
    data = [entetes]
    for date_str_ligne, libelle, avant, credit, debit, apres in lignes:
        data.append([
            date_str_ligne,
            libelle,
            avant,
            credit,
            debit,
            apres,
        ])
    data.append(["", "TOTAL :", "", formater_nombre(total_credit), formater_nombre(total_debit), ""])

    col_widths = [22 * mm, 55 * mm, 28 * mm, 20 * mm, 20 * mm, 28 * mm]
    mouvements_table = Table(data, colWidths=col_widths, repeatRows=1)

    style_commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("SPAN", (0, -1), (1, -1)),  # fusionne Date + Libellé sur la ligne TOTAL
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    mouvements_table.setStyle(TableStyle(style_commands))
    story.append(mouvements_table)

    doc.title = f"Historique des mouvements - {client.nom_client} {client.prenom_client}"
    doc.author = "AFG Bank"
    doc.subject = "Historique des mouvements de titres"

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def formater_nombre(n):
    if n is None:
        return ""
    return f"{n:,}".replace(",", " ")


def nombre_en_lettres_fr(n):
    texte = num2words(n, lang="fr")
    texte = texte.replace("-", " ")
    return texte[0].upper() + texte[1:]


def _construire_styles():
    styles_base = getSampleStyleSheet()
    style_normal = ParagraphStyle("normal", parent=styles_base["Normal"], fontSize=9.5, leading=13)
    style_titre = ParagraphStyle(
        "titre", parent=styles_base["Heading1"], alignment=TA_CENTER,
        fontSize=13, spaceAfter=2,
    )
    style_soustitre = ParagraphStyle(
        "soustitre", parent=style_normal, alignment=TA_CENTER,
        fontSize=10, fontName="Helvetica-Bold",
    )
    style_date_droite = ParagraphStyle("date_droite", parent=style_normal, alignment=TA_RIGHT)
    style_montant = ParagraphStyle(
        "montant", parent=style_normal, fontName="Helvetica-Bold", fontSize=10.5,
    )
    return style_normal, style_titre, style_soustitre, style_date_droite, style_montant


def _construire_bloc_certificat(portefeuille, styles, numero_certificat):
    """Construit les flowables composant UN exemplaire du certificat."""
    style_normal, style_titre, style_soustitre, style_date_droite, style_montant = styles

    client = portefeuille.client
    titre = portefeuille.titre

    nb_actions = portefeuille.nb_titre
    valeur_nominale_unitaire = getattr(titre, "nominal", 0) or 0
    valeur_nominale_totale = nb_actions * valeur_nominale_unitaire

    story = []

    date_str = f"Libreville, le {date.today().strftime('%d/%m/%Y')}"
    story.append(Paragraph(date_str, style_date_droite))
    story.append(Spacer(1, 4))

    if os.path.exists(LOGO_PATH):
        logo_gauche = Image(LOGO_PATH, width=26 * mm, height=13 * mm)
        logo_droite = Image(LOGO_PATH, width=26 * mm, height=13 * mm)
    else:
        logo_gauche = Paragraph("", style_normal)
        logo_droite = Paragraph("", style_normal)

    titre_bloc = [
        Paragraph(f"Certificat d'Actions du Titre {titre.libelle.upper()}", style_titre),
        Paragraph(f"N° : {numero_certificat}", style_soustitre),
    ]

    entete_table = Table(
        [[logo_gauche, titre_bloc, logo_droite]],
        colWidths=[33 * mm, 112 * mm, 33 * mm],
    )
    entete_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(entete_table)
    story.append(Spacer(1, 10))

    # --- Titulaire ---
    nom_complet = getattr(client, "nom_complet", None) or f"{client.nom_client} {client.prenom_client}".strip()
    adresse = getattr(client, "adresse", "") or ""
    telephone = getattr(client, "tel_client", "") or ""

    titulaire_table = Table(
        [
            [Paragraph(f"Nom du titulaire : <b>{nom_complet}</b>", style_normal), ""],
            [Paragraph(f"Adresse : {adresse}", style_normal),
             Paragraph(f"Tél. : {telephone}", style_normal)],
        ],
        colWidths=[110 * mm, 68 * mm],
    )
    titulaire_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(titulaire_table)
    story.append(Spacer(1, 6))

    lettres = nombre_en_lettres_fr(nb_actions)
    libelle_action = "action nominative" if nb_actions == 1 else "actions nominatives"

    propriete_table = Table(
        [[
            Paragraph("Est propriétaire de", style_normal),
            Paragraph(f"<b>{lettres}</b>", style_montant),
            Paragraph(f"{libelle_action} de F CFA", style_normal),
        ]],
        colWidths=[35 * mm, 75 * mm, 68 * mm],
    )
    propriete_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))
    story.append(propriete_table)
    story.append(Spacer(1, 2))

    valeur_table = Table(
        [[
            Paragraph(f"<b>{formater_nombre(valeur_nominale_totale)}</b>", style_montant),
            Paragraph("comme indiquées ci-dessous :", style_normal),
        ]],
        colWidths=[35 * mm, 143 * mm],
    )
    story.append(valeur_table)
    story.append(Spacer(1, 10))

    # --- Tableau Identifiant actionnaire / Nombre d'actions (centré) ---
    id_table = Table(
        [
            ["Identifiant actionnaire", "Nombre d'actions"],
            [str(client.get_id()), str(nb_actions)],
        ],
        colWidths=[45 * mm, 45 * mm],
        hAlign="CENTER",
    )
    id_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(id_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Ce certificat annule et remplace tous les autres certificats précédemment délivrés par AFG Bank",
        style_normal,
    ))
    story.append(Spacer(1, 22))

    signatures_table = Table(
        [["Signature", "Signature"]],
        colWidths=[89 * mm, 89 * mm],
    )
    signatures_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(signatures_table)

    return story


def generer_certificat_actions_pdf(portefeuille):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = _construire_styles()
    story = []

    numero_certificat = generer_numero_certificat()

    story.extend(_construire_bloc_certificat(portefeuille, styles, numero_certificat))

    story.append(Spacer(1, 22 * mm))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black))
    story.append(Spacer(1, 22 * mm))

    story.extend(_construire_bloc_certificat(portefeuille, styles, numero_certificat))

    doc.title = f"Certificat d'actions - {portefeuille.client.nom_client} {portefeuille.client.prenom_client}"
    doc.author = "AFG Bank"
    doc.subject = "Historique des mouvements de titres"

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def fmt_montant(valeur):
    if valeur is None:
        valeur = 0
    entier = int(round(valeur))
    s = f"{entier:,}".replace(",", " ")
    return f"{s} FCFA"


def fmt_pct(valeur):
    if valeur is None:
        return ""
    if float(valeur) == int(valeur):
        return f"{int(valeur)}%"
    return f"{valeur}%"


def draw_avis_block(c: canvas.Canvas, ctx: dict, page_width, top_y, block_height):

    margin_left = 12 * mm   # ↓ réduit de 18 à 12 mm : tableaux plus larges
    margin_right = 12 * mm  # ↓ réduit de 18 à 12 mm
    content_width = page_width - margin_left - margin_right

    def Y(offset_mm):
        """Convertit un offset (mm, positif vers le bas) depuis le haut du bloc en coordonnée absolue."""
        return top_y - offset_mm * mm

    # --- Logo (à droite) ---
    logo_w, logo_h = 30 * mm, 14 * mm
    logo_x = page_width - margin_right - logo_w
    logo_y = Y(1) - logo_h
    try:
        c.drawImage(
            LOGO_PATH,
            logo_x, logo_y,
            width=logo_w, height=logo_h,
            preserveAspectRatio=True,
            anchor="n",
            mask="auto",
        )
    except Exception:
        c.setFillColor(colors.HexColor("#E0302D"))
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(page_width - margin_right, Y(5), "AFG")
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(page_width - margin_right, Y(8.5), "BANK")
        c.setFont("Helvetica-Oblique", 5.5)
        c.drawRightString(page_width - margin_right, Y(11.5), "Atlantic Group")

    # --- Titre encadré (centré) ---
    box_w, box_h = 62 * mm, 8 * mm
    box_x = (page_width - box_w) / 2
    box_y = Y(9)
    c.rect(box_x, box_y, box_w, box_h)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(box_x + box_w / 2, box_y + box_h / 2 - 3, "AVIS DE TRANSACTION")

    # --- Sous-titre ---
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_width / 2, Y(15), ctx["operation_label"])

    # --- Bloc date (gauche) / identité client (droite) ---
    col2_x = margin_left + 88 * mm

    c.setFont("Helvetica", 7.5)
    c.drawString(margin_left, Y(20.5), f"Libreville, le :  {ctx['date']}")

    cy = 20.5
    c.setFont("Helvetica", 7.5)
    for line in ctx["client_lines"]:
        c.drawString(col2_x, Y(cy), line)
        cy += 3.6
    client_block_end = cy

    # --- Texte d'intro ---
    verbe = "au CREDIT" if ctx["sens"] == "CREDIT" else "au DEBIT"
    intro_lines = [
        "Nous avons l'honneur de vous faire connaître que nous",
        f"inscrivons {verbe} de votre compte le montant de",
        "l'opération ci-dessous exécutée ce jour selon vos instructions.",
    ]
    c.setFont("Helvetica", 6.8)
    iy = 26
    for line in intro_lines:
        c.drawString(margin_left, Y(iy), line)
        iy += 3.1

    # --- Numéro de client / compte ---
    c.setFont("Helvetica", 7.5)
    c.drawString(margin_left, Y(38), "Numéro de client")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(margin_left, Y(41.5), ctx["numero_client"])

    c.setFont("Helvetica", 7.5)
    c.drawString(margin_left, Y(46.5), "Numéro de compte")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(margin_left, Y(50), ctx["numero_compte"])

    # --- Tableau principal ---
    table_x = col2_x
    table_w = (page_width - margin_right) - col2_x
    col1_w = table_w * 0.42
    col2_w = table_w * 0.28
    col3_w = table_w * 0.30

    row_h = 4.3  # mm

    def hline(off_mm, x0, x1):
        c.line(x0, Y(off_mm), x1, Y(off_mm))

    def row(off_top_mm, h_mm, label, col2, col3, bold=False):
        y_text = Y(off_top_mm + h_mm - 1.6)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 7.5)
        c.drawString(table_x + 1.5 * mm, y_text, label)
        if col2 is not None:
            c.drawCentredString(table_x + col1_w + col2_w / 2, y_text, col2)
        if col3 is not None:
            c.drawRightString(table_x + col1_w + col2_w + col3_w - 1.5 * mm, y_text, col3)

    t = client_block_end + 1.5

    headA_w = table_w * 0.40
    headB_w = table_w * 0.28
    headC_w = table_w * 0.32

    head_top = t
    head_bottom = t + 2 * row_h

    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(table_x + headA_w / 2, Y(t + row_h - 1.6), "Montant de l'opération")
    c.drawCentredString(table_x + headA_w + headB_w / 2, Y(t + row_h - 1.6), "Nombre d'actions")
    c.drawCentredString(table_x + headA_w + headB_w + headC_w / 2, Y(t + row_h - 1.6), "Total")
    t += row_h

    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(table_x + headA_w / 2, Y(t + row_h - 1.6),
                         fmt_montant(ctx["montant_operation"]).replace(" FCFA", ""))
    c.drawCentredString(table_x + headA_w + headB_w / 2, Y(t + row_h - 1.6), str(ctx["nb_actions"]))
    c.drawCentredString(table_x + headA_w + headB_w + headC_w / 2, Y(t + row_h - 1.6), fmt_montant(ctx["total"]))
    t += row_h + 1.5

    c.rect(table_x, Y(head_bottom), table_w, (head_bottom - head_top) * mm)
    hline(head_top + row_h, table_x, table_x + table_w)
    c.line(table_x + headA_w, Y(head_bottom), table_x + headA_w, Y(head_top))
    c.line(table_x + headA_w + headB_w, Y(head_bottom), table_x + headA_w + headB_w, Y(head_top))

    box_top = t
    lines = [
        ("Commission AFG BANK HT", fmt_pct(ctx["commission_ht_pct"]), fmt_montant(ctx["commission_ht"]), False),
        ("TVA", fmt_pct(ctx["tva_pct"]), fmt_montant(ctx["tva"]), False),
        ("CSS", fmt_pct(ctx["css_pct"]), fmt_montant(ctx["css"]), False),
        ("Commission AFG BANK TTC", "", fmt_montant(ctx["commission_ttc"]), True),
    ]
    for label, pct, montant, bold in lines:
        row(t, row_h, label, pct, montant, bold=bold)
        t += row_h
    box_bottom = t
    c.rect(table_x, Y(box_bottom), table_w, (box_bottom - box_top) * mm)

    t += 1.5

    # --- Bloc plus-value / IRCM ---
    box2_top = t
    if ctx.get("plus_value_pct") is not None:
        row(t, row_h, "Plus value de cession", str(ctx["plus_value_nb"]), fmt_montant(ctx["plus_value_montant"]))
        t += row_h
        row(t, row_h, "IRCM", fmt_pct(ctx["ircm_pct"]), fmt_montant(ctx["ircm_montant"]), bold=True)
        t += row_h
    else:
        t += row_h * 2
    box2_bottom = t
    c.rect(table_x, Y(box2_bottom), table_w, (box2_bottom - box2_top) * mm)

    t += 1.5

    row_h_final = 5.5
    row(t, row_h_final, ctx["label_final"], None, fmt_montant(ctx["montant_final"]), bold=True)
    c.rect(table_x, Y(t + row_h_final), table_w, row_h_final * mm)
    t += row_h_final

    gap_after_table = 50
    footer_height = 8

    footer_top_offset = t + gap_after_table
    footer_bottom_offset = footer_top_offset + footer_height

    c.rect(margin_left, Y(footer_bottom_offset), content_width, footer_height * mm)
    c.setFont("Helvetica", 6)
    c.drawCentredString(
        page_width / 2, Y(footer_top_offset + 3),
        "Ce document a été établi par le service titres de AFG BANK et ne nécessite pas de signature.",
    )
    c.drawCentredString(
        page_width / 2, Y(footer_top_offset + 6),
        "Toute réclamation devra être effectuée dans un délai de 5 jours ouvrés à compter de la réception du présent document.",
    )

    separator_offset = block_height / mm
    c.setDash(2, 2)
    c.line(margin_left, Y(separator_offset), page_width - margin_right, Y(separator_offset))
    c.setDash()

def draw_avis_page(c: canvas.Canvas, ctx: dict, page_width, page_height):

    margin_top = 8 * mm
    margin_bottom = 8 * mm
    usable_height = page_height - margin_top - margin_bottom
    block_height = usable_height / 2

    # Copie du haut
    draw_avis_block(c, ctx, page_width, page_height - margin_top, block_height)
    # Copie du bas
    draw_avis_block(c, ctx, page_width, page_height - margin_top - block_height, block_height)


def generate_avis_pdf(vendeur_ctx: dict, acheteur_ctx: dict, output_path: str):

    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    draw_avis_page(c, vendeur_ctx, page_width, page_height)
    c.showPage()

    draw_avis_page(c, acheteur_ctx, page_width, page_height)
    c.showPage()

    c.save()
    return output_path

def _client_lines(client, adresse_extra=None):
    lines = [str(client)]
    if adresse_extra:
        lines.extend(adresse_extra)
    return lines


def _safe_call(value, default=""):
    if callable(value):
        value = value()
    return value if value not in (None, "") else default


def build_contexts_from_operation(operation):

    date_str = operation.date_ordre.strftime("%d/%m/%Y") if operation.date_ordre else ""

    montant_operation = operation.cours_operation or 0
    nb_actions = operation.nb_titre or 0
    total = operation.brut if operation.brut is not None else montant_operation * nb_actions

    commission_ht = operation.commission or 0
    tva = operation.tax or 0
    css = float(operation.css or 0)
    commission_ttc = commission_ht + tva + css

    ircm_montant = operation.ircm or 0

    if (operation.sens or "").upper().startswith("VENTE"):
        vendeur_client = operation.client
        acheteur_client = operation.beneficiaire
    else:
        vendeur_client = operation.beneficiaire
        acheteur_client = operation.client

    montant_credit_vendeur = total - commission_ttc - ircm_montant
    montant_debit_acheteur = total + commission_ttc

    op_labelle_vend = "Vente de titres"
    op_labelle_ben = "Achat"
    if operation.type_operation.libelle == "Transfert de titres":
        op_labelle_vend = "Transfert de titres"
        op_labelle_ben = "Transfert de titres"


    vendeur_ctx = {
        "date": date_str,
        "operation_label": op_labelle_vend,
        "sens": "CREDIT",
        "client_lines": _client_lines(vendeur_client),
        "numero_client": _safe_call(getattr(vendeur_client, "numero_client", "")),
        "numero_compte": _safe_call(getattr(vendeur_client, "num_compte", "")),
        "montant_operation": montant_operation,
        "nb_actions": nb_actions,
        "total": total,
        "commission_ht_pct": 1,
        "commission_ht": commission_ht,
        "tva_pct": 18,
        "tva": tva,
        "css_pct": 1,
        "css": css,
        "commission_ttc": commission_ttc,
        "plus_value_pct": 0,
        "plus_value_nb": nb_actions,
        "plus_value_montant": 0,
        "ircm_pct": 20,
        "ircm_montant": ircm_montant,
        "montant_final": montant_credit_vendeur,
        "label_final": "Crédit compte client",
    }

    acheteur_ctx = {
        "date": date_str,
        "operation_label": op_labelle_ben,
        "sens": "DEBIT",
        "client_lines": _client_lines(acheteur_client),
        "numero_client": _safe_call(getattr(acheteur_client, "numero_client", "")),
        "numero_compte": _safe_call(getattr(acheteur_client, "num_compte", "")),
        "montant_operation": montant_operation,
        "nb_actions": nb_actions,
        "total": total,
        "commission_ht_pct": 1,
        "commission_ht": commission_ht,
        "tva_pct": 18,
        "tva": tva,
        "css_pct": 1,
        "css": css,
        "commission_ttc": commission_ttc,
        "plus_value_pct": None,
        "plus_value_nb": None,
        "plus_value_montant": None,
        "ircm_pct": 20,
        "ircm_montant": 0,
        "montant_final": montant_debit_acheteur,
        "label_final": "Débit compte client",
    }

    return vendeur_ctx, acheteur_ctx