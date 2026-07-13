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


# from django.db import IntegrityError, transaction
#
#     cursor1 = connection1.cursor()
#     cursor1.execute("SELECT * FROM HISTO_ORDRES")
#     Operation.objects.all().delete()
#
#     stats = {
#         'total': 0,
#         'ok': 0,
#         'etablissement_manquant': 0,
#         'client_manquant': 0,
#         'type_titre_manquant': 0,
#         'titre_manquant': 0,
#         'integrity_error': 0,
#         'autre_erreur': 0,
#     }
#
#     erreurs_detail = []
#
#     for row in cursor1:
#         stats['total'] += 1
#
#         try:
#             etablissement = Etablissement.objects.get(old_id=row[0])
#         except Etablissement.DoesNotExist:
#             stats['etablissement_manquant'] += 1
#             erreurs_detail.append(('etablissement_manquant', row[0:4]))
#             continue
#
#         try:
#             client = Client.objects.get(old_id=row[1], banque=etablissement)
#         except Client.DoesNotExist:
#             stats['client_manquant'] += 1
#             erreurs_detail.append(('client_manquant', row[0:4]))
#             continue
#
#         try:
#             type_titre = TypeTitre.objects.get(old_id=row[2])
#         except TypeTitre.DoesNotExist:
#             stats['type_titre_manquant'] += 1
#             erreurs_detail.append(('type_titre_manquant', row[0:4]))
#             continue
#
#         try:
#             titre = Titre.objects.get(old_id=row[3])
#         except Titre.DoesNotExist:
#             stats['titre_manquant'] += 1
#             erreurs_detail.append(('titre_manquant', row[0:4]))
#             continue
#
#         try:
#             with transaction.atomic():
#                 Operation.objects.create(
#                     etablissement=etablissement, client=client, type_titre=type_titre, titre=titre,
#                     num_ordre=row[4], num_seq_ordre=row[5], nb_titre=row[6], sens=row[7],
#                     cours_operation=row[8], date_ordre=row[9], code_op=row[10], date_creat=row[11],
#                     brut=row[12], commission=row[13], tax=row[14], ordre_valide=row[15], ordre_ben=row[16],
#                     old_id_ets_ben=row[17], old_id_sous_ben=row[18], code_op_ben=row[19], nbportef=row[20],
#                     date_modif=row[21], nom_creat=row[22], nom_modif=row[23], nbportefben=row[24],
#                     nbencours=row[25], ircm=row[30], css=row[31]
#                 )
#             stats['ok'] += 1
#         except IntegrityError as e:
#             stats['integrity_error'] += 1
#             erreurs_detail.append(('integrity_error', row, str(e)))
#         except Exception as e:
#             stats['autre_erreur'] += 1
#             erreurs_detail.append(('autre_erreur', row, str(e)))
#
#     # Résumé
#     print("=" * 50)
#     print(f"Total lignes source     : {stats['total']}")
#     print(f"Importées avec succès   : {stats['ok']}")
#     print(f"Etablissement manquant  : {stats['etablissement_manquant']}")
#     print(f"Client manquant         : {stats['client_manquant']}")
#     print(f"Type titre manquant     : {stats['type_titre_manquant']}")
#     print(f"Titre manquant          : {stats['titre_manquant']}")
#     print(f"Erreurs d'intégrité     : {stats['integrity_error']}")
#     print(f"Autres erreurs          : {stats['autre_erreur']}")
#     print("=" * 50)





