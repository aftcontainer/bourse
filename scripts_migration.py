import oracledb

from mainapp.models import Client, CategorieClient, Qualite, Pays

connection1 = oracledb.connect(
    user="BOURUSER",
    password="Afri2012",
    host="192.168.1.102",
    port=1521,
    service_name="BOURSE"
)
############ Migration de la table client #####################
cursor1 = connection1.cursor()
cursor1.execute("SELECT * FROM INDEX")
Client.objects.all().delete()

cursor1.close()

############ Fin migration de la table client #####################
############ Fin migration de la table portefeuille #####################
# cursor1 = connection1.cursor()
# cursor1.execute("SELECT * FROM CPTTITRE")
#
#
# Portefeuille.objects.all().delete()
#
# for row in cursor1:
#     try:
#         etablissement = Etablissement.objects.get(old_id=row[0])
#     except Etablissement.DoesNotExist:
#         print(f"⚠️ Etablissement introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
#         continue
#
#     try:
#         client = Client.objects.get(old_id=row[1], banque=etablissement)
#     except Client.DoesNotExist:
#         print(f"⚠️ Client introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
#         continue
#
#     titre = None
#     if row[3]:
#         try:
#             titre = Titre.objects.get(old_id=row[3])
#         except Titre.DoesNotExist:
#             print(f"⚠️ Titre introuvable pour old_id='{row[3]}' (pf old_id={row[0]})")
#
#     Portefeuille.objects.create(
#         etablissement=etablissement, client=client,
#         titre=titre, nb_titre=row[5],
#         dernier_mouv=row[6], nom_creat=row[7],
#         date_creat=row[8], nom_modif=row[9],
#         date_modif=row[10]
#     )
#
# cursor1.close()

############ Fin migration de la table IndexTitre #####################
# cursor1 = connection1.cursor()
# cursor1.execute("SELECT * FROM INDEXTITRE")
# IndexTitre.objects.all().delete()
#
# for row in cursor1:
#     try:
#         etablissement = Etablissement.objects.get(old_id=row[0])
#     except Etablissement.DoesNotExist:
#         print(f"⚠️ Etablissement introuvable pour old_id='{row[0]}' (etablissement old_id={row[0]})")
#         continue
#     try:
#         client = Client.objects.get(old_id=row[1], banque=etablissement)
#     except Client.DoesNotExist:
#         print(f"⚠️ Client introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
#         continue
#     try:
#         titre = Titre.objects.get(old_id=row[3])
#     except Client.DoesNotExist:
#         print(f"⚠️ Titre introuvable pour old_id='{row[3]}' (etablissement old_id={row[3]})")
#         continue
#     try:
#         IndexTitre.objects.create(
#             client=client, etablissement=etablissement, titre=titre, indordre=row[4],
#             nb_titre=row[5], debut_index=row[6], fin_index=row[7], statut_tire=row[8], nom_creat=row[9],
#             date_creat=row[10], nom_modif=row[11], date_modif=row[12]
#         )
#     except Exception as e:
#         print(e)
#         print("Echec de la création de l'index")





