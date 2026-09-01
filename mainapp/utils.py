from django.utils import timezone
from django.db.models import Max

from mainapp.models import IndexTitre, Portefeuille, Operation, SequenceCertificat, SequenceOrdre

from django.db import transaction


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def get_error_message_from_form(form):
    errors = []
    for field, field_errors in form.errors.items():
        errors.extend(field_errors)
    return errors[0]

def save_with_audit(form, user):
    obj = form.save(commit=False)

    if obj.pk is None:
        obj.user_id = user.id

    obj.updated_by = user.id
    obj.save()

    return obj

def repartir_plages(vendeur, acheteur, titre, nb_titres):
    """
    Déplace nb_titres du vendeur vers l'acheteur.
    Les titres sont pris dans les plages les plus anciennes.
    """

    with transaction.atomic():

        plages = (
            IndexTitre.objects
            .filter(portefeuille__client=vendeur,
                    portefeuille__titre=titre)
            .order_by("debut")
        )

        portef_acheteur = Portefeuille.objects.get(
            client=acheteur,
            titre=titre
        )

        restant = nb_titres

        for plage in plages:

            if restant == 0:
                break

            taille = plage.fin - plage.debut + 1

            # La plage entière est transférée
            if taille <= restant:

                IndexTitre.objects.create(
                    portefeuille=portef_acheteur,
                    debut=plage.debut,
                    fin=plage.fin
                )

                restant -= taille

                plage.delete()

            # Une partie seulement est transférée
            else:

                nouveau_debut = plage.fin - restant + 1

                IndexTitre.objects.create(
                    portefeuille=portef_acheteur,
                    debut=nouveau_debut,
                    fin=plage.fin
                )

                plage.fin = nouveau_debut - 1
                plage.save()

                restant = 0

        if restant > 0:
            raise Exception("Le vendeur ne possède pas assez de titres.")

def derniere_annee_op():
    derniere_date = (
        Operation.objects
        .exclude(date_ordre__isnull=True)
        .aggregate(Max('date_ordre'))['date_ordre__max']
    )
    return derniere_date.year if derniere_date else timezone.now().year

def generer_numero_certificat():
    numero = SequenceCertificat.prochain_numero()
    return f"{numero:06d}"

def generer_numero_ordre():
    numero = SequenceOrdre.prochain_numero()
    return f"{numero:06d}"