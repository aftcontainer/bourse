import oracledb

from mainapp.models import Client, CategorieClient, Qualite, Pays, Devise, Etablissement, TypeTitre, Titre, \
    TypeOperation, Operation, CategorieAction, Ville, Portefeuille, IndexTitre

connection1 = oracledb.connect(
    user="BOURUSER",
    password="Afri2012",
    host="192.168.1.104",
    port=1521,
    service_name="BOURSE"
)

############ Migration de la table DEVISE #####################

def recharger_devises():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM DEVISE")
    Devise.objects.all().delete()

    for row in cursor1:
        Devise.objects.create(old_id=row[0], libelle=row[1], code_devise=row[3])

############ Migration de la table ETABLISSEMENT #####################

def recharger_etablissements():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM ORGANISME")
    Etablissement.objects.all().delete()

    for row in cursor1:
        try:
            devise = Devise.objects.get(old_id=row[1])
        except Devise.DoesNotExist:
            if devise:
                print('#############################')
                print(f"devise {devise.old_id}")
                print('#############################')
            else:
                print('Dévise non recupérée')
        Etablissement.objects.create(
            devise=devise,old_id=row[0],libelle=row[1],adresse=row[2],bp_etablissement=row[3],
            tx_commission=row[5],tx_tax=row[6],nom_creat=row[7],date_creat=row[8],nom_modif=row[9],
            date_modif=row[10],type_com=row[12],plafond_commission=row[13],tx_commission2=row[14],
            plafond_commission2=row[15],tx_commission3=row[16],plafond_commission3=row[17],
            min_commission=row[18],tx_retro=row[19],mt_retro=row[20],sigle=row[21],min_retro=row[22],
            orgaprinc=row[23],orga_fin=row[24]
        )

############ Migration de la table QUALITE #####################

def recharger_qualites():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM QUALITE")
    Qualite.objects.all().delete()

    for row in cursor1:
        Qualite.objects.create(old_id=row[0],libelle=row[1])

############ Migration de la table CATEGORIE_CLIENT #####################

def recharger_cat_clients():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM CATEGORIE")
    CategorieClient.objects.all().delete()

    for row in cursor1:
        Qualite.objects.create(
            old_id=row[0], libelle=row[1],nom_creat=row[2],
            date_creat=row[3],nom_modif=row[4],date_modif=row[5]
        )

############ Migration de la table TYPE_OPERATION #####################

def charger_types_operations():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM OPE")
    TypeOperation.objects.all().delete()

    for row in cursor1:

        TypeOperation.objects.create(
            old_id=row[0],libelle=row[1],nom_creat=row[2],date_creat=row[3],
            nom_modif=row[4],date_modif=row[5],mvnt_operation=row[6],
            commission=row[7],tva=row[8],css=row[9],rcm=row[10]
        )

############ Migration de la table CATEGORIE_ACTION #####################

def charger_cat_actions():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM CATEGORIEACTION")
    CategorieAction.objects.all().delete()

    for row in cursor1:
        CategorieAction.objects.create(code_cat=row[0],libelle_cat=row[1])

############ Migration de la table TYPE_ACTION #####################

def charger_type_actions():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM TYPETITRE")
    TypeTitre.objects.all().delete()

    for row in cursor1:
        CategorieAction.objects.create(
            old_id=row[0],libelle=row[1],nom_creat=row[2],date_creat=row[3],
            nom_modif=row[4],date_modif=row[5]
        )

############ Migration de la table TITRE #####################

def charger_titres():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM TITRES")
    Titre.objects.all().delete()

    for row in cursor1:

        try:
            type_titre = TypeTitre.objects.get(old_id=row[0])
        except TypeTitre.DoesNotExist:
            print("Echec de recupération du type")
            continue

        try:
            devise = Devise.objects.get(old_id=row[4])
        except TypeTitre.DoesNotExist:
            print("Echec de recupération du type")
            continue

        try:
            Titre.objects.create(
                type_titre=type_titre, old_id=row[1], libelle=row[2], nominal=row[3],
                devise=devise, quotite=row[5], nb_mini=row[6], cours=row[7], cours_oblig=row[8],
                tx_oblig=row[9], datech=row[10], nom_creat=row[11], date_creat=row[12],
                nom_modif=row[13], date_modif=row[14], dercoupon=row[16], min_ann=row[17],
                max_ann=row[18], nb_actions=row[19], tx_visa=row[20], date_inf=row[21]
            )
        except Exception as e:
            print(e)

############ Migration de la table CLIENT #####################

def charger_clients():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM REFCLIENT")
    Client.objects.all().delete()
    i=0

    qualite = None
    for row in cursor1:
        try:
            banque = Etablissement.objects.get(old_id=row[3])
        except Etablissement.DoesNotExist:
            print("Echec de recupération du l'établissement")
            continue

        try:
            if row[21]:
                qualite = Qualite.objects.get(old_id=row[21])
        except Qualite.DoesNotExist:
            print("Echec de recupération du la qualité")
            continue

        try:
            cat_client = CategorieClient.objects.get(old_id=row[1])
        except CategorieClient.DoesNotExist:
            print("Echec de recupération du la catégorie")
            continue

        try:
            Client.objects.create(
                old_id=row[0],category_client=cat_client,nom_client=row[2],banque=banque,
                prenom_client=row[4],adresse=row[5],bp_client=row[6],ville=row[7],
                tel_client=row[8],fax_client=row[9],tx_commission=row[10],exonerer_taxe=row[11],
                nom_creat=row[12],date_creat=row[13],nom_modif=row[14],date_modif=row[15],
                date_naissance=row[16],lieu_naissance=row[17],num_carte=row[18],
                matricule=row[19],num_compte=row[20],qualite=qualite,email_client=row[24],
                site_client=row[25],nature_carte=row[26],indentifiant=row[31]
            )
            print(f"{i+1}")
            i+=1
        except Exception as e:
            print(e)
            print("Echec de l'enregistrement du client")

############ Migration de la table PORTEFEUILLE #####################

def charger_comptes():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM CPTTITRE")

    Portefeuille.objects.all().delete()
    i = 0

    for row in cursor1:
        try:
            etablissement = Etablissement.objects.get(old_id=row[0])
        except Etablissement.DoesNotExist:
            print(f"⚠️ Etablissement introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
            continue

        try:
            if Client.objects.filter(old_id=row[1], banque=etablissement).count()<2:
                client = Client.objects.get(old_id=row[1], banque=etablissement)
        except Client.DoesNotExist:
            print(f"⚠️ Client introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
            continue

        titre = None
        if row[3]:
            try:
                titre = Titre.objects.get(old_id=row[3])
            except Titre.DoesNotExist:
                print(f"⚠️ Titre introuvable pour old_id='{row[3]}' (pf old_id={row[0]})")
        if Client.objects.filter(old_id=row[1], banque=etablissement).count() < 2:
            Portefeuille.objects.create(
                etablissement=etablissement, client=client,
                titre=titre, nb_titre=row[5],
                dernier_mouv=row[6], nom_creat=row[7],
                date_creat=row[8], nom_modif=row[9],
                date_modif=row[10]
            )
            print(f"{i+1}")
            i+=1
        else:
            #Faire les enregistrements manuellement
            pass

    cursor1.close()

########### Fin migration de la table IndexTitre #####################
def charger_index():
    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM INDEXTITRE")
    IndexTitre.objects.all().delete()

    for row in cursor1:
        try:
            etablissement = Etablissement.objects.get(old_id=row[0])
        except Etablissement.DoesNotExist:
            print(f"⚠️ Etablissement introuvable pour old_id='{row[0]}' (etablissement old_id={row[0]})")
            continue
        try:
            if Client.objects.filter(old_id=row[1], banque=etablissement).count() < 2:
                client = Client.objects.get(old_id=row[1], banque=etablissement)
        except Client.DoesNotExist:
            print(f"⚠️ Client introuvable pour old_id='{row[1]}' (etablissement old_id={row[0]})")
            continue
        try:
            titre = Titre.objects.get(old_id=row[3])
        except Titre.DoesNotExist:
            print(f"⚠️ Titre introuvable pour old_id='{row[3]}' (etablissement old_id={row[3]})")
            continue
        try:
            if Client.objects.filter(old_id=row[1], banque=etablissement).count() < 2:
                IndexTitre.objects.create(
                    client=client, etablissement=etablissement, titre=titre, indordre=row[4],
                    debut_index=row[6], fin_index=row[7], statut_tire=row[8], nom_creat=row[9],
                    date_creat=row[10], nom_modif=row[11], date_modif=row[12]
                )
        except Exception as e:
            print(e)
            print("Echec de la création de l'index")


def recharger_operations1():
    from django.db import IntegrityError, transaction

    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM HISTO_ORDRES")
    Operation.objects.all().delete()

    stats = {
        'total': 0,
        'ok': 0,
        'etablissement_manquant': 0,
        'client_manquant': 0,
        'type_titre_manquant': 0,
        'titre_manquant': 0,
        'integrity_error': 0,
        'autre_erreur': 0,
    }

    erreurs_detail = []

    for row in cursor1:
        stats['total'] += 1

        try:
            etablissement = Etablissement.objects.get(old_id=row[0])
        except Etablissement.DoesNotExist:
            stats['etablissement_manquant'] += 1
            erreurs_detail.append(('etablissement_manquant', row[0:4]))
            continue

        try:
            if Client.objects.filter(old_id=row[1], banque=etablissement).count() < 2:
                client = Client.objects.get(old_id=row[1], banque=etablissement)
        except Client.DoesNotExist:
            if client:
                print('#############################')
                print(f"client {client.old_id}")
                print(f"etablissement_id {etablissement.old_id}")
                print('#############################')
            else:
                print('Non recupéré')

            stats['client_manquant'] += 1
            erreurs_detail.append(('client_manquant', row[0:4]))
            continue

        try:
            type_titre = TypeTitre.objects.get(old_id=row[2])
        except TypeTitre.DoesNotExist:
            stats['type_titre_manquant'] += 1
            erreurs_detail.append(('type_titre_manquant', row[0:4]))
            continue

        try:
            titre = Titre.objects.get(old_id=row[3])
        except Titre.DoesNotExist:
            stats['titre_manquant'] += 1
            erreurs_detail.append(('titre_manquant', row[0:4]))
            continue

        try:
            type_op = TypeOperation.objects.filter(old_id=row[10]).first()
        except Titre.DoesNotExist:
            stats['type_op'] += 1
            erreurs_detail.append(('type_op', row[0:4]))
            continue

        try:
            with transaction.atomic():
                etb_client = None
                code_benef = None
                num_ordre = row[4]
                code_op = type_op.old_id
                if type_op.mvnt_operation == 'D':
                    etb_benef = etablissement
                    mon_benef = client
                    code_benef = code_op
                else:
                    mon_client = client
                    etb_client = etablissement
                    code_client = code_op
                if Client.objects.filter(old_id=row[1], banque=etablissement).count() < 2:
                    if not Operation.objects.filter(num_ordre=num_ordre).exists():
                        print('Partie 1')
                        Operation.objects.create(
                            etablissement=etb_client, client=mon_client, type_titre=type_titre, titre=titre,
                            num_ordre=num_ordre, num_seq_ordre=row[5], nb_titre=row[6], sens=type_op.mvnt_operation,
                            cours_operation=row[8], date_ordre=row[9], code_op=code_client, date_creat=row[11],
                            brut=row[12], commission=row[13], tax=row[14], ordre_valide=row[15], ordre_ben=row[16],
                            old_id_ets_ben=row[17], old_id_sous_ben=row[18], code_op_ben=code_benef, nbportef=row[20],
                            date_modif=row[21], nom_creat=row[22], nom_modif=row[23], nbportefben=row[24],
                            nbencours=row[25], ircm=row[30], css=row[31], beneficiaire=mon_benef,
                            etablissement_ben=etb_benef, type_operation=type_op
                        )
                    else:
                        print('Partie 2')
                        op = Operation.objects.filter(num_ordre=num_ordre).first()
                        op.etablissement = etb_client;
                        op.client = mon_client;
                        op.type_titre = type_titre
                        op.titre = titre;
                        op.num_ordre = num_ordre;
                        op.num_seq_ordre = row[5];
                        op.nb_titre = row[6]
                        op.sens = type_op.mvnt_operation;
                        op.cours_operation = row[8];
                        op.date_ordre = row[9];
                        op.code_op = row[10]
                        op.date_creat = row[11];
                        op.brut = row[12];
                        op.commission = row[13];
                        op.tax = row[14]
                        op.ordre_valide = row[15];
                        op.ordre_ben = row[16];
                        op.old_id_ets_ben = row[17]
                        op.old_id_sous_ben = row[18];
                        op.code_op_ben = row[19];
                        op.nbportef = row[20]
                        op.date_modif = row[21];
                        op.nom_creat = row[22];
                        op.nom_modif = row[23];
                        op.nbportefben = row[24]
                        op.nbencours = row[25];
                        op.ircm = row[30];
                        op.css = row[31];
                        op.beneficiaire = mon_benef
                        op.etablissement_ben = etb_benef
                        op.save()

            stats['ok'] += 1
        except IntegrityError as e:
            print(e)
            stats['integrity_error'] += 1
            print('**********************************')
            erreurs_detail.append(('integrity_error', row, str(e)))
            print(f"client {client.old_id}")
            print(f"etablissement_id {etablissement.old_id}")
            print('**********************************')
        except Exception as e:
            print(e)
            stats['autre_erreur'] += 1
            erreurs_detail.append(('autre_erreur', row, str(e)))
            print('##################################')
            erreurs_detail.append(('integrity_error', row, str(e)))
            print(f"client {client.old_id}")
            print(f"etablissement_id {etablissement.old_id}")
            print('##################################')

    # Résumé
    print("=" * 50)
    print(f"Total lignes source     : {stats['total']}")
    print(f"Importées avec succès   : {stats['ok']}")
    print(f"Etablissement manquant  : {stats['etablissement_manquant']}")
    print(f"Client manquant         : {stats['client_manquant']}")
    print(f"Type titre manquant     : {stats['type_titre_manquant']}")
    print(f"Titre manquant          : {stats['titre_manquant']}")
    print(f"Erreurs d'intégrité     : {stats['integrity_error']}")
    print(f"Autres erreurs          : {stats['autre_erreur']}")
    print("=" * 50)

from datetime import date


def recharger_operations():
    from django.db import IntegrityError, transaction

    cursor1 = connection1.cursor()
    cursor1.execute("SELECT * FROM HISTO_ORDRES")

    Operation.objects.all().delete()

    stats = {
        "total": 0,
        "ok": 0,
        "etablissement_manquant": 0,
        "client_manquant": 0,
        "type_titre_manquant": 0,
        "titre_manquant": 0,
        "type_op_manquant": 0,
        "integrity_error": 0,
        "autre_erreur": 0,
    }

    erreurs_detail = []

    for row in cursor1:

        stats["total"] += 1

        try:

            try:
                etablissement = Etablissement.objects.get(old_id=row[0])
            except Etablissement.DoesNotExist:
                stats["etablissement_manquant"] += 1
                erreurs_detail.append(("etablissement_manquant", row[0:4]))
                continue

            clients = Client.objects.filter(
                old_id=row[1],
                banque=etablissement
            )

            nb_clients = clients.count()

            if nb_clients == 0:
                stats["client_manquant"] += 1
                erreurs_detail.append(("client_manquant", row[0:4]))
                continue

            if nb_clients > 1:
                print(
                    f"Plusieurs clients trouvés "
                    f"(old_id={row[1]}, banque={etablissement.old_id})"
                )
                continue

            client = clients.first()

            try:
                type_titre = TypeTitre.objects.get(old_id=row[2])
            except TypeTitre.DoesNotExist:
                stats["type_titre_manquant"] += 1
                erreurs_detail.append(("type_titre_manquant", row[0:4]))
                continue

            try:
                titre = Titre.objects.get(old_id=row[3])
            except Titre.DoesNotExist:
                stats["titre_manquant"] += 1
                erreurs_detail.append(("titre_manquant", row[0:4]))
                continue

            #############################################
            # TYPE OPERATION
            #############################################

            type_op = TypeOperation.objects.filter(
                old_id=row[10]
            ).first()

            if type_op is None:
                stats["type_op_manquant"] += 1
                erreurs_detail.append(("type_op_manquant", row[0:4]))
                continue

            #############################################
            # INITIALISATION DES VARIABLES
            #############################################

            num_ordre = row[4]

            mon_client = None
            mon_benef = None

            etb_client = None
            etb_benef = None

            code_client = None
            code_benef = None

            code_op = type_op.old_id

            if type_op.mvnt_operation == "D":

                mon_benef = client
                etb_benef = etablissement
                code_benef = code_op

            else:

                mon_client = client
                etb_client = etablissement
                code_client = code_op

            with transaction.atomic():

                operation = Operation.objects.filter(
                    num_ordre=num_ordre
                ).first()

                # ---- Partie 2 ici ----

            if operation is None:

                print(f"Création de l'ordre {num_ordre}")

                operation = Operation.objects.create(

                    etablissement=etb_client,
                    client=mon_client,
                    beneficiaire=mon_benef,
                    etablissement_ben=etb_benef,

                    type_operation=type_op,
                    type_titre=type_titre,
                    titre=titre,

                    num_ordre=num_ordre,
                    num_seq_ordre=row[5],

                    nb_titre=row[6],
                    sens=type_op.mvnt_operation,

                    cours_operation=row[8],
                    date_ordre=row[9],

                    code_op=code_client,
                    code_op_ben=code_benef,

                    date_creat=row[11],

                    brut=row[12],
                    commission=row[13],
                    tax=row[14],

                    ordre_valide=row[15],
                    ordre_ben=row[16],

                    old_id_ets_ben=row[17],
                    old_id_sous_ben=row[18],

                    nbportef=row[20],
                    date_modif=row[21],

                    nom_creat=row[22],
                    nom_modif=row[23],

                    nbportefben=row[24],
                    nbencours=row[25],

                    ircm=row[30],
                    css=row[31],
                )


            else:

                print(f"Mise à jour de l'ordre {num_ordre}")

                if mon_client is not None:
                    operation.client = mon_client
                    operation.etablissement = etb_client
                    operation.code_op = code_client

                if mon_benef is not None:
                    operation.beneficiaire = mon_benef
                    operation.etablissement_ben = etb_benef
                    operation.code_op_ben = code_benef

                operation.type_operation = type_op
                operation.type_titre = type_titre
                operation.titre = titre

                operation.num_seq_ordre = row[5]
                operation.nb_titre = row[6]
                operation.sens = type_op.mvnt_operation

                operation.cours_operation = row[8]
                operation.date_ordre = row[9]

                operation.date_creat = row[11]

                operation.brut = row[12]
                operation.commission = row[13]
                operation.tax = row[14]

                operation.ordre_valide = row[15]
                operation.ordre_ben = row[16]

                operation.old_id_ets_ben = row[17]
                operation.old_id_sous_ben = row[18]

                operation.nbportef = row[20]
                operation.date_modif = row[21]

                operation.nom_creat = row[22]
                operation.nom_modif = row[23]

                operation.nbportefben = row[24]
                operation.nbencours = row[25]

                operation.ircm = row[30]
                operation.css = row[31]

                operation.save()

            stats["ok"] += 1
            ############################################################
            # GESTION DES ERREURS
            ############################################################

        except IntegrityError as e:

            stats["integrity_error"] += 1

            erreurs_detail.append({
                "type": "IntegrityError",
                "num_ordre": row[4],
                "client": row[1],
                "etablissement": row[0],
                "message": str(e),
            })

            print("=" * 80)
            print("ERREUR D'INTEGRITE")
            print(f"Num ordre      : {row[4]}")
            print(f"Client ancien  : {row[1]}")
            print(f"Etablissement  : {row[0]}")
            print(e)
            print("=" * 80)

        except Exception as e:

            stats["autre_erreur"] += 1

            erreurs_detail.append({
                "type": "Exception",
                "num_ordre": row[4],
                "client": row[1],
                "etablissement": row[0],
                "message": str(e),
            })

            print("=" * 80)
            print("AUTRE ERREUR")
            print(f"Num ordre      : {row[4]}")
            print(f"Client ancien  : {row[1]}")
            print(f"Etablissement  : {row[0]}")
            print(e)
            print("=" * 80)

    ############################################################
    # RESUME
    ############################################################

    print()
    print("=" * 80)
    print("FIN DU RECHARGEMENT DES OPERATIONS")
    print("=" * 80)

    print(f"Total lignes source     : {stats['total']}")
    print(f"Importées               : {stats['ok']}")
    print(f"Etablissement manquant  : {stats['etablissement_manquant']}")
    print(f"Client manquant         : {stats['client_manquant']}")
    print(f"Type titre manquant     : {stats['type_titre_manquant']}")
    print(f"Titre manquant          : {stats['titre_manquant']}")
    print(f"Type opération manquant : {stats['type_op_manquant']}")
    print(f"Erreurs intégrité       : {stats['integrity_error']}")
    print(f"Autres erreurs          : {stats['autre_erreur']}")

    print("=" * 80)

    if erreurs_detail:

        print()
        print("DETAIL DES ERREURS")
        print("=" * 80)

        for erreur in erreurs_detail:
            print(erreur)

    print("=" * 80)




