import oracledb
import os
import json
import io
from io import BytesIO

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import Permission
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Max, Q, Count
from django.http import JsonResponse, HttpResponse, FileResponse
import secrets

from django.conf import settings

from django.utils.http import urlsafe_base64_decode
from datetime import date

from django.views.decorators.http import require_POST

from mainapp.forms import SignInForm, DeviseForm, QualiteForm, CategorieClientForm, TypeOperationForm, TypeTitreForm, \
    TitreForm, EtablissementForm, UserForm, ClientForm, RoleForm, VenteEtTransfertForm, PortefeuilleForm
from .models import Devise, Qualite, CategorieClient, TypeOperation, TypeTitre, Titre, Etablissement, Client, User, \
    Portefeuille, Role, JournalAudit, UserRole, Operation, IndexTitre

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages

from .services import GestionIndexTitre, nombre_en_lettres, formater_nombre, construire_pdf_registre_central, \
    generer_historique_mouvements_pdf, generer_certificat_actions_pdf, build_contexts_from_operation, generate_avis_pdf
from .utils import is_ajax, get_error_message_from_form, save_with_audit, derniere_annee_op

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from collections import OrderedDict

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .tasks import email_activation_compte

from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from weasyprint import HTML

# connection1 = oracledb.connect(
#     user="BOURUSER",
#     password="Afri2012",
#     host="192.168.1.104",
#     port=1521,
#     service_name="BOURSE"
# )

LOGO_PATH = os.path.join(settings.BASE_DIR, "static", "mainapp/logos", "logo_AFG_Bank.png")

def se_connecter(request):
    form = SignInForm()
    if request.method == "POST":
        form = SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(email=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    next_url = request.GET.get('next', reverse('mainapp:home'))
                    return redirect(next_url)
                else:
                    messages.add_message(request, messages.WARNING,
                                         "Vous n'etes pas actif. Veuillez contacter l'administrateur")
                    return render(request, "login.html", {"form": form})
            else:
                messages.add_message(request, messages.ERROR, "Login ou mot de passe inconnu")
                return render(request, "login.html", {"form": form})
        else:
            messages.add_message(request, messages.WARNING, "Veuillez vérifier les informations et continuer.")
            return render(request, "login.html", {"form": form})
    return render(request,"login.html",{"form": form})

def se_deconnecter(request):
    logout(request)
    return redirect('mainapp:connexion')

@login_required(login_url="/connexion")
def home(request):

    nb_titres = Titre.objects.all().count()
    nb_operations = Operation.objects.all().count()
    nb_clients = Client.objects.all().count()
    operations = Operation.objects.order_by("-id")[:5]
    nb_etablissements = Etablissement.objects.all().count()
    dernier_an_op = derniere_annee_op()

    Operation.objects.all().update(est_valide=True)

    return render(
            request, "home.html",
            {
                "nb_titres":nb_titres,
                "nb_operations": nb_operations,
                "nb_clients": nb_clients,
                "operations": operations,
                "nb_etablissements": nb_etablissements,
                "dernier_an_op": dernier_an_op
            }
        )


def operations_par_mois(request):
    annee_courante = derniere_annee_op()

    MOIS_FR = [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
    ]

    stats = (
        Operation.objects
        .filter(date_ordre__year=annee_courante)
        .annotate(mois=TruncMonth('date_ordre'))
        .values('mois')
        .annotate(
            total=Count('id'),
            nb_transfert=Count(
                'id', filter=Q(type_operation__libelle='Transfert de titres')
            ),
            nb_vente=Count(
                'id', filter=Q(Q(type_operation__libelle='Vente de titres') | Q(type_operation__libelle='Achat de titres'))
            ),
        )
        .order_by('mois')
    )

    resultats = OrderedDict()
    for m in range(1, 13):
        resultats[m] = {'total': 0, 'nb_transfert': 0, 'nb_vente': 0}

    for s in stats:
        resultats[s['mois'].month] = {
            'total': s['total'],
            'nb_transfert': s['nb_transfert'],
            'nb_vente': s['nb_vente'],
        }

    data = {
        'annee': annee_courante,
        'labels': [MOIS_FR[m - 1] for m in resultats.keys()],
        'totaux': [v['total'] for v in resultats.values()],
        'transferts': [v['nb_transfert'] for v in resultats.values()],
        'ventes': [v['nb_vente'] for v in resultats.values()],
    }

    return JsonResponse(data)

@login_required(login_url="/connexion")
def donnees(request):
    return render(request,"donnees.html")

@login_required(login_url="/connexion")
def impressions(request):
    return render(request,"impressions.html")

@login_required(login_url="/connexion")
def parametres(request):
    return render(request,"parametres.html")

@permission_required('mainapp.view_devise')
@login_required(login_url="/connexion")
def liste_devises(request):
    devises = Devise.objects.all().order_by("libelle")
    if is_ajax(request) and request.method == "POST":
        if request.POST.get("action") == "delete":
            devise = get_object_or_404(Devise, id=request.POST.get("id"))
            try:
                devise.delete()
                return JsonResponse({"msg": "Devise supprimée avec succès", "status": "success"})
            except Exception:
                return JsonResponse({"msg": "Suppression impossible (devise utilisée ?)", "status": "error"})
        devise_id = request.POST.get('id')
        if devise_id:
            devise = get_object_or_404(Devise,id=devise_id)
            form = DeviseForm(request.POST,instance=devise)
            msg = "Devise modifiée avec succès"
        else:
            form = DeviseForm(request.POST)
            msg = "Devise enregistrée avec succès"
        if form.is_valid():
            try:
                save_with_audit(form,request.user)
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_devises.html", {"devises": devises})

@permission_required('mainapp.view_qualite')
@login_required(login_url="/connexion")
def liste_qualites(request):
    qualites = Qualite.objects.all().order_by("libelle")
    if is_ajax(request) and request.method == "POST":
        if request.POST.get("action") == "delete":
            qualite = get_object_or_404(Qualite, id=request.POST.get("id"))
            try:
                qualite.delete()
                return JsonResponse({"msg": "qualité supprimée avec succès", "status": "success"})
            except Exception:
                return JsonResponse({"msg": "Suppression impossible (qualité utilisée ?)", "status": "error"})
        qualite_id = request.POST.get('id')
        if qualite_id:
            qualite = get_object_or_404(Qualite,id=qualite_id)
            form = QualiteForm(request.POST,instance=qualite)
            msg = "Qualité modifiée avec succès"
        else:
            form = QualiteForm(request.POST)
            msg = "qualité enregistrée avec succès"
        if form.is_valid():
            try:
                save_with_audit(form,request.user)
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_qualites.html", {"qualites": qualites})

@permission_required('mainapp.view_categorieclient')
@login_required(login_url="/connexion")
def liste_categories_clients(request):
    cats = CategorieClient.objects.all().order_by("libelle")
    if is_ajax(request) and request.method == "POST":
        if request.POST.get("action") == "delete":
            cat_client = get_object_or_404(CategorieClient, id=request.POST.get("id"))
            try:
                cat_client.delete()
                return JsonResponse({"msg": "catégorie de client supprimée avec succès", "status": "success"})
            except Exception:
                return JsonResponse({"msg": "Suppression impossible (catégorie de client utilisée ?)", "status": "error"})
        cat_client_id = request.POST.get('id')
        if cat_client_id:
            cat_client = get_object_or_404(CategorieClient,id=cat_client_id)
            form = CategorieClientForm(request.POST,instance=cat_client)
            msg = "catégorie de client modifiée avec succès"
        else:
            form = CategorieClientForm(request.POST)
            msg = "catégorie de client enregistrée avec succès"
        if form.is_valid():
            try:
                save_with_audit(form,request.user)
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_cat_clients.html", {"cats": cats})

@permission_required('mainapp.view_typeoperation')
@login_required(login_url="/connexion")
def liste_t_operations(request):
    t_operations = TypeOperation.objects.all().order_by("libelle")
    if is_ajax(request) and request.method == "POST":
        if request.POST.get("action") == "delete":
            t_operations = get_object_or_404(TypeOperation, id=request.POST.get("id"))
            try:
                t_operations.delete()
                return JsonResponse({"msg": "type d'opération supprimé avec succès", "status": "success"})
            except Exception:
                return JsonResponse({"msg": "Suppression impossible (type d'opération utilisé ?)", "status": "error"})
    return render(request, "liste_types_operations.html", {"t_operations": t_operations})

@permission_required('mainapp.add_typeoperation')
@login_required(login_url="/connexion")
def creer_t_operation(request):
    form = TypeOperationForm()
    if request.method == "POST":
        form = TypeOperationForm(request.POST)
        if form.is_valid():
            obj = save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_t_operation',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "erreur")
            return render(request,"creer_t_operation.html",{"form": form})
    return render(request,"creer_t_operation.html",{"form": form})

@permission_required('mainapp.change_typeoperation')
@login_required(login_url="/connexion")
def editer_t_operation(request,public_id):
    obj = TypeOperation.objects.get(public_id=public_id)
    form = TypeOperationForm(instance=obj)
    if request.method == "POST":
        form = TypeOperationForm(request.POST,instance=obj)
        if form.is_valid():
            save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_t_operation',kwargs={'public_id':obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "editer_t_operation.html", {"form": form,"obj": obj})
    return render(request, "editer_t_operation.html", {"form": form,"obj": obj})

@permission_required('mainapp.view_typeoperation')
@login_required(login_url="/connexion")
def details_t_operation(request,public_id):
    obj = TypeOperation.objects.get(public_id=public_id)
    return render(request, "details_t_operation.html", {"obj": obj})

@permission_required('mainapp.view_typetitre')
@login_required(login_url="/connexion")
def liste_t_titres(request):
    t_titres = TypeTitre.objects.all().order_by('libelle')
    if is_ajax(request) and request.method == "POST":
        if request.POST.get("action") == "delete":
            t_titre = get_object_or_404(TypeTitre, id=request.POST.get("id"))
            try:
                t_titre.delete()
                return JsonResponse({"msg": "type de titre supprimé avec succès", "status": "success"})
            except Exception:
                return JsonResponse({"msg": "Suppression impossible (type de titre utilisé ?)", "status": "error"})
        t_titre_id = request.POST.get('id')
        if t_titre_id:
            t_titre = get_object_or_404(TypeTitre,id=t_titre_id)
            form = TypeTitreForm(request.POST,instance=t_titre)
            msg = "type de titre modifié avec succès"
        else:
            form = TypeTitreForm(request.POST)
            msg = "type de titre enregistré avec succès"
        if form.is_valid():
            try:
                save_with_audit(form,request.user)
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_t_titres.html", {"t_titres": t_titres})

@permission_required('mainapp.view_titre')
@login_required(login_url="/connexion")
def liste_titres(request):
    titres = Titre.objects.all().order_by('libelle')
    return render(request,"liste_titres.html",{"titres": titres})

@permission_required('mainapp.add_titre')
@login_required(login_url="/connexion")
def creer_titre(request):
    form = TitreForm()
    if request.method == "POST":
        form = TitreForm(request.POST)
        if form.is_valid():
            obj = save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_titre',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "creer_titre.html", {"form": form})
    else:
        return render(request, "creer_titre.html", {"form": form})

@permission_required('mainapp.change_devise')
@login_required(login_url="/connexion")
def editer_titre(request,public_id):
    obj = Titre.objects.get(public_id=public_id)
    form = TitreForm(instance=obj)
    if request.method == "POST":
        form = TitreForm(request.POST,instance=obj)
        if form.is_valid():
            save_with_audit(form,request.user)
            return redirect(reverse('mainapp:liste_titres'))
        messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
        return render(request, "editer_titre.html", {"form": form,"obj": obj})
    return render(request, "editer_titre.html", {"form": form, "obj": obj})

@permission_required('mainapp.view_titre',login_url="/connexion")
@login_required(login_url="/connexion")
def details_titre(request,public_id):
    obj = Titre.objects.get(public_id=public_id)
    return render(request,"details_titre.html",{"obj": obj})

@permission_required('mainapp.view_etablissement',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_ets(request):
    ets = Etablissement.objects.all().order_by('libelle')
    return render(request,"liste_ets.html",{"ets": ets})

@permission_required('mainapp.add_etablissement',login_url="/connexion")
@login_required(login_url="/connexion")
def creer_ets(request):
    form = EtablissementForm()
    if request.method == "POST":
        form = EtablissementForm(request.POST)
        if form.is_valid():
            obj = save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_ets',kwargs={'public_id':obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "creer_ets.html", {"form": form})
    return render(request, "creer_ets.html", {"form": form})

@permission_required('mainapp.change_etablissement',login_url="/connexion")
@login_required(login_url="/connexion")
def editer_ets(request,public_id):
    obj = Etablissement.objects.get(public_id=public_id)
    form = EtablissementForm(instance=obj)
    if request.method == "POST":
        form = EtablissementForm(request.POST,instance=obj)
        if form.is_valid():
            save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_ets',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "editer_ets.html", {"form": form})
    return render(request, "editer_ets.html", {"form": form})

@permission_required('mainapp.view_etablissement',login_url="/connexion")
@login_required(login_url="/connexion")
def details_ets(request,public_id):
    obj = Etablissement.objects.get(public_id=public_id)
    return render(request,"details_ets.html",{"obj": obj})

@login_required(login_url="/connexion")
def gestion_utilisateurs(request):
    return render(request,"gestion_users.html")

@permission_required('mainapp.view_user',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_utilisateurs(request):
    users = User.objects.all().order_by('last_name')
    return render(request,"liste_users.html",{"users": users})

@permission_required('mainapp.add_user',login_url="/connexion")
@login_required(login_url="/connexion")
def creer_utilisateur(request):
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = secrets.token_urlsafe(8)
            user.set_password(password)
            user.is_active = True
            user.created_by = request.user.id
            user.updated_by = request.user.id
            user.save()
            domaine = request.get_host()
            email_activation_compte.delay(domaine, user.email, password)
            return redirect(reverse("mainapp:attribuer_user_role",kwargs={"public_id":user.public_id}))
        else:
            msg = get_error_message_from_form(form)
            messages.add_message(request, messages.WARNING,msg)
            return render(request, "creer_utilisateur.html", {"form": form})
    else:
        return render(request, "creer_utilisateur.html", {"form": form})

@require_POST
def toggle_utilisateur_actif(request, public_id):

    utilisateur = get_object_or_404(User, public_id=public_id)

    # Empêche de se désactiver soi-même par erreur
    if utilisateur.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("mainapp:details_utilisateur", public_id=utilisateur.public_id)

    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save(update_fields=["is_active"])

    if utilisateur.is_active:
        messages.success(
            request,
            f"Le compte de {utilisateur.first_name} {utilisateur.last_name} a été activé."
        )
    else:
        messages.success(
            request,
            f"Le compte de {utilisateur.first_name} {utilisateur.last_name} a été désactivé."
        )

    return redirect("mainapp:details_utilisateur", public_id=utilisateur.public_id)

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None:
        if user.is_active == False:
            user.is_active = True
        return redirect(reverse("mainapp:connexion"))
    else:
        return HttpResponse("Lien d'activation invalide.")

@permission_required('mainapp.view_client',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_clients(request):
    titres = Titre.objects.all()
    return render(request,"liste_clients.html",{"titres": titres})

@permission_required('mainapp.view_client',login_url="/connexion")
@login_required(login_url="/connexion")
def clients_data(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search = request.GET.get("search[value]", "")

    qs = Client.objects.select_related(
        "category_client",
        "banque",
    ).order_by("-created")

    # Recherche DataTables
    if search:
        qs = qs.filter(
            Q(category_client__libelle__icontains=search) |
            Q(nom_client__icontains=search) |
            Q(prenom_client__icontains=search) |
            Q(ville__icontains=search) |
            Q(banque__libelle__icontains=search)
        )

    records_filtered = qs.count()

    # Nombre total avant recherche
    records_total = Client.objects.count()

    data = []

    for client in qs[start:start + length]:

        # Catégorie
        if client.category_client:
            categorie_client = client.category_client.libelle
        else:
            categorie_client = "Non renseigné"

        # Etablissement
        if client.banque:
            etablissement = client.banque.libelle
        else:
            etablissement = "Non renseigné"

        # Ville
        if client.ville:
            ville = client.ville
        else:
            ville = "Non renseigné"

        # Date
        if client.created:
            date_operation = client.created.strftime("%d/%m/%Y")
        else:
            date_operation = ""

        data.append([
            start + len(data) + 1,
            categorie_client,
            client.nom_client +"  "+client.prenom_client,
            etablissement,
            ville,
            date_operation,
            f"""
                <a href="donnees/souscripteurs/{client.public_id}"
                   class="btn btn-icon btn-light btn-active-light-primary btn-sm"
                   data-bs-toggle="tooltip"
                   title="Voir les détails">

                    <i class="ki-duotone ki-eye fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                    </i>

                </a>
                
                <a href="donnees/souscripteurs/{client.public_id}/editer" 
                    class="btn btn-icon editBtn btn-light btn-active-light-primary btn-sm me-1"
                   data-bs-toggle="tooltip" title="Modifier">
                    <i class="ki-duotone ki-pencil fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                    </i>
                </a>
                """
        ])

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@login_required(login_url="/connexion")
def liste_clients_ets(request,public_id):
    ets = get_object_or_404(Etablissement,public_id=public_id)
    return render(request,"liste_souscripteurs_ets.html",{'ets': ets})

@login_required(login_url="/connexion")
def clients_ets_data(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search = request.GET.get("search[value]", "")
    ets_public_id = (request.GET.get("public_id") or "").strip()

    if not ets_public_id:
        return JsonResponse({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "public_id manquant ou invalide",
        }, status=400)

    ets = get_object_or_404(Etablissement, public_id=ets_public_id)

    qs = Portefeuille.objects.filter(etablissement=ets).select_related(
        "client", "titre"
    ).order_by('client__nom_client', 'client__prenom_client')

    # Recherche DataTables
    if search:
        qs = qs.filter(
            Q(client__category_client__libelle__icontains=search) |
            Q(client__nom_client__icontains=search) |
            Q(client__prenom_client__icontains=search) |
            Q(client__ville__icontains=search) |
            Q(client__banque__libelle__icontains=search)
        )

    records_filtered = qs.count()
    records_total = Portefeuille.objects.filter(etablissement=ets).count()

    data = []

    for compte in qs[start:start + length]:

        categorie_client = compte.client.category_client.libelle if compte.client.category_client else "Non renseigné"
        num_compte = compte.client.num_compte if compte.client.num_compte else "Non renseigné"
        ville = compte.client.ville or "Non renseigné"
        nb_actions = compte.nb_titre if compte.nb_titre else "0"

        data.append([
            start + len(data) + 1,
            num_compte,
            categorie_client,
            f"{compte.client.nom_client}  {compte.client.prenom_client}",
            ville,
            nb_actions,
            f"""
                <a href="/donnees/souscripteurs/{compte.client.public_id}"
                   class="btn btn-icon btn-light btn-active-light-primary btn-sm"
                   data-bs-toggle="tooltip"
                   title="Voir les détails">
                    <i class="ki-duotone ki-eye fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                    </i>
                </a>
                <a href="/donnees/souscripteurs/{compte.client.public_id}/editer"
                    class="btn btn-icon editBtn btn-light btn-active-light-primary btn-sm me-1"
                   data-bs-toggle="tooltip" title="Modifier">
                    <i class="ki-duotone ki-pencil fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                    </i>
                </a>
                """
        ])

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@login_required(login_url="/connexion")
def liste_clients_titre(request,public_id):
    titre = get_object_or_404(Titre,public_id=public_id)
    return render(request,"liste_souscripteurs_titre.html",{'titre': titre})

@login_required(login_url="/connexion")
def clients_titre_data(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search = request.GET.get("search[value]", "")
    titre_public_id = (request.GET.get("public_id") or "").strip()

    if not titre_public_id:
        return JsonResponse({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "public_id manquant ou invalide",
        }, status=400)

    titre = get_object_or_404(Titre, public_id=titre_public_id)

    qs = Portefeuille.objects.filter(titre=titre).select_related(
        "client", "etablissement"
    ).order_by('client__nom_client', 'client__prenom_client')

    # Recherche DataTables
    if search:
        qs = qs.filter(
            Q(client__category_client__libelle__icontains=search) |
            Q(client__nom_client__icontains=search) |
            Q(client__prenom_client__icontains=search) |
            Q(client__ville__icontains=search) |
            Q(client__banque__libelle__icontains=search)
        )

    records_filtered = qs.count()
    records_total = Portefeuille.objects.filter(titre=titre).count()

    data = []

    for compte in qs[start:start + length]:

        categorie_client = compte.client.category_client.libelle if compte.client.category_client else "Non renseigné"
        etablissement = compte.etablissement.libelle if compte.etablissement else "Non renseigné"
        ville = compte.client.ville or "Non renseigné"
        nb_actions = compte.nb_titre or 0

        data.append([
            start + len(data) + 1,
            categorie_client,
            f"{compte.client.nom_client}  {compte.client.prenom_client}",
            etablissement,
            ville,
            nb_actions,
            f"""
                <a href="/donnees/souscripteurs/{compte.client.public_id}"
                   class="btn btn-icon btn-light btn-active-light-primary btn-sm"
                   data-bs-toggle="tooltip"
                   title="Voir les détails">
                    <i class="ki-duotone ki-eye fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                    </i>
                </a>
                <a href="/donnees/souscripteurs/{compte.client.public_id}/editer"
                    class="btn btn-icon editBtn btn-light btn-active-light-primary btn-sm me-1"
                   data-bs-toggle="tooltip" title="Modifier">
                    <i class="ki-duotone ki-pencil fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                    </i>
                </a>
                """
        ])

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@permission_required('mainapp.view_client',login_url="/connexion")
@login_required(login_url="/connexion")
def creer_souscripteur(request):
    form = ClientForm()
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            save_with_audit(form,request.user)
            return render(request,"liste_clients.html",{"clients": Client.objects.all()})
        else:
            msg = get_error_message_from_form(form)
            messages.add_message(request, messages.WARNING, msg)
            return render(request, "creer_souscripteur.html", {"form": form})
    else:
        return render(request, "creer_souscripteur.html", {"form": form})

@permission_required('mainapp.view_client',login_url="/connexion")
@login_required(login_url="/connexion")
def editer_souscripteur(request,public_id):
    obj = Client.objects.get(public_id=public_id)
    form = ClientForm(instance=obj)
    if request.method == "POST":
        form = ClientForm(request.POST,instance=obj)
        if form.is_valid():
            obj = save_with_audit(form,request.user)
            return redirect(reverse('mainapp:details_souscripteur',kwargs={'public_id':obj.public_id}))
        msg = get_error_message_from_form(form)
        messages.add_message(request, messages.WARNING, msg)
        return render(request, "editer_souscripteur.html", {"form": form})
    return render(request, "editer_souscripteur.html", {"form": form})

@permission_required('mainapp.view_client',login_url="/connexion")
@login_required(login_url="/connexion")
def details_souscripteur(request,public_id):
    obj = Client.objects.get(public_id=public_id)
    return render(request,"details_souscripteur.html",{"obj": obj,"form_portefeuille": PortefeuilleForm(),})

@permission_required('mainapp.view_portefeuille',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_comptes(request):
    comptes = Portefeuille.objects.all()
    return render(request,"liste_comptes.html",{"comptes": comptes})

@permission_required('mainapp.view_portefeuille',login_url="/connexion")
@login_required(login_url="/connexion")
def comptes_data(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search = request.GET.get("search[value]", "")

    qs = Portefeuille.objects.select_related(
        "client",
        "titre",
        "etablissement"
    ).order_by("-created")

    # Recherche DataTables
    if search:
        qs = qs.filter(
            Q(client__nom_client__contains=search) |
            Q(client__prenom_client__icontains=search) |
            Q(titre__type_titre__libelle__icontains=search) |
            Q(etablissement__libelle__contains=search) |
            Q(created__icontains=search)
        )

    records_filtered = qs.count()

    # Nombre total avant recherche
    records_total = Portefeuille.objects.count()

    data = []

    for compte in qs[start:start + length]:

        # client
        if compte.client.nom_client:
            nom_client = compte.client.nom_client
        else:
            nom_client = ""

        # client
        if compte.client.prenom_client:
            prenom_client = compte.client.prenom_client
        else:
            prenom_client = ""

        # Ville
        if compte.titre:
            if compte.titre.type_titre:
                type_titre = compte.titre.type_titre.libelle
            else:
                type_titre = "Non renseigné"
        else:
            type_titre = "Non renseigné"

        if compte.etablissement:
            etablissement = compte.etablissement.libelle
        else:
            etablissement = "Non renseigné"

        # Date
        if compte.created:
            date_creation = compte.created.strftime("%d/%m/%Y")
        else:
            date_creation = "Non renseignée"

        data.append([
            start + len(data) + 1,
            nom_client+" "+prenom_client,
            type_titre,
            etablissement,
            compte.nb_titre,
            date_creation,
            f"""
                <a href="donnees/compte/{compte.public_id}"
                   class="btn btn-icon btn-light btn-active-light-primary btn-sm"
                   data-bs-toggle="tooltip"
                   title="Voir les détails">

                    <i class="ki-duotone ki-eye fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                    </i>

                </a>

                <a href="donnees/comptes/{compte.public_id}/editer" 
                    class="btn btn-icon editBtn btn-light btn-active-light-primary btn-sm me-1"
                   data-bs-toggle="tooltip" title="Modifier">
                    <i class="ki-duotone ki-pencil fs-4">
                        <span class="path1"></span>
                        <span class="path2"></span>
                    </i>
                </a>
                """
        ])

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })


@permission_required('mainapp.view_portefeuille',login_url="/connexion")
@login_required(login_url="/connexion")
def details_compte(request,public_id):
    obj = Portefeuille.objects.get(public_id=public_id)
    return render(request,"details_compte.html",{"obj": obj})

@permission_required('mainapp.view_role',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_roles(request):
    roles = Role.objects.all().order_by("libelle")
    return render(request,"liste_roles.html",{"roles": roles})

STANDARD_ACTIONS = ('view', 'add', 'change', 'delete')

def _build_permissions_by_model(selected_ids=None):
    selected_ids = selected_ids or []
    app_models = apps.get_app_config('mainapp').get_models()

    permissions_by_model = []
    extra_permissions = []

    for model in app_models:
        ct = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(content_type=ct)

        perms_map = {}
        custom_perms = []

        for p in perms:
            action = p.codename.split('_')[0]
            if action in STANDARD_ACTIONS and p.codename == f"{action}_{model._meta.model_name}":
                perms_map[action] = p
            else:
                custom_perms.append(p)

        permissions_by_model.append({
            'label': model._meta.verbose_name.capitalize(),
            'model_name': model._meta.model_name,
            'perms': perms_map,
            'custom_perms': custom_perms,
        })

        extra_permissions.extend(custom_perms)

    permissions_by_model.sort(key=lambda m: m['label'])
    return permissions_by_model

# def _build_permissions_by_model(selected_ids=None):
#     """Construit la matrice module -> {view, add, change, delete}."""
#     selected_ids = selected_ids or []
#     app_models = apps.get_app_config('mainapp').get_models()
#
#     permissions_by_model = []
#     for model in app_models:
#         ct = ContentType.objects.get_for_model(model)
#         perms = Permission.objects.filter(content_type=ct)
#         perms_map = {p.codename.split('_')[0]: p for p in perms}
#         permissions_by_model.append({
#             'label': model._meta.verbose_name.capitalize(),
#             'model_name': model._meta.model_name,
#             'perms': perms_map,
#         })
#
#     permissions_by_model.sort(key=lambda m: m['label'])
#     return permissions_by_model

@permission_required('mainapp.add_role',login_url="/connexion")
@login_required(login_url="/connexion")
def creer_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = save_with_audit(form,request.user)

            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            role.is_active = True
            save_with_audit(form,request.user)
            messages.success(request, f"Le rôle « {role.libelle} » a été créé avec succès.")
            return redirect('mainapp:liste_roles')
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = RoleForm()

    context = {
        'form': form,
        'permissions_by_model': _build_permissions_by_model(),
        'selected_permission_ids': [],
    }
    return render(request, 'creer_role.html', context)


@permission_required('mainapp.view_role',login_url="/connexion")
@login_required(login_url="/connexion")
def editer_role(request, public_id):
    role = get_object_or_404(Role, public_id=public_id)

    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = save_with_audit(form,request.user)
            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            role.is_active = True
            role.save()
            messages.success(request, f"Le rôle « {role.libelle} » a été mis à jour.")
            return redirect('mainapp:liste_roles')
    else:
        form = RoleForm(instance=role)

    context = {
        'form': form,
        'role': role,
        'permissions_by_model': _build_permissions_by_model(),
        'selected_permission_ids': list(role.permissions.values_list('id', flat=True)),
    }
    return render(request, 'creer_role.html', context)


def journal_audit(request):
    logs_qs = JournalAudit.objects.select_related('user', 'content_type').order_by('-created')

    action = request.GET.get('action')
    if action:
        logs_qs = logs_qs.filter(action=action)

    user_id = request.GET.get('user')
    if user_id:
        logs_qs = logs_qs.filter(user_id=user_id)

    model_name = request.GET.get('model')
    if model_name:
        logs_qs = logs_qs.filter(content_type__model=model_name)

    q = request.GET.get('q')
    if q:
        logs_qs = logs_qs.filter(object_repr__icontains=q)

    date_debut = request.GET.get('date_debut')
    if date_debut:
        logs_qs = logs_qs.filter(created__date__gte=date_debut)

    date_fin = request.GET.get('date_fin')
    if date_fin:
        logs_qs = logs_qs.filter(created__date__lte=date_fin)

    paginator = Paginator(logs_qs, 50)
    page_number = request.GET.get('page', 1)
    logs = paginator.get_page(page_number)

    # Querystring sans le paramètre "page", pour les liens de pagination
    querystring = request.GET.copy()
    querystring.pop('page', None)

    context = {
        'logs': logs,
        'querystring': querystring.urlencode(),
        'action_choices': JournalAudit.ACTION_CHOICES,
        'utilisateurs': User.objects.all().order_by('last_name', 'first_name'),
        'modeles': (
            JournalAudit.objects
            .exclude(content_type__isnull=True)
            .values_list('content_type__model', flat=True)
            .distinct()
            .order_by('content_type__model')
        ),
    }
    return render(request, 'journal_audit.html', context)

@permission_required('mainapp.change_role',login_url="/connexion")
@login_required(login_url="/connexion")
@login_required(login_url="/connexion")
def attribuer_role(request):
    utilisateurs_qs = User.objects.all().order_by('last_name', 'first_name')
    roles_qs = Role.objects.filter(is_active=True).order_by('libelle')

    utilisateurs = []
    for u in utilisateurs_qs:
        role_ids = list(
            UserRole.objects.filter(user=u).values_list('role_id', flat=True)
        )
        u.role_ids_csv = ','.join(str(rid) for rid in role_ids)
        u.roles_display = list(
            Role.objects.filter(id__in=role_ids).values_list('libelle', flat=True)
        )
        utilisateurs.append(u)

    selected_user = None
    selected_role_ids = []

    # Utilisateur pré-sélectionné via ?user=<id> (lien "Modifier" du tableau)
    user_id = request.GET.get('user') or request.POST.get('user')
    if user_id:
        selected_user = get_object_or_404(User, id=user_id)
        selected_role_ids = list(
            UserRole.objects.filter(user=selected_user).values_list('role_id', flat=True)
        )

    if request.method == 'POST':
        selected_user = get_object_or_404(User, id=request.POST.get('user'))
        role_ids = request.POST.getlist('roles')

        # Remplace entièrement les rôles de l'utilisateur par la sélection
        UserRole.objects.filter(user=selected_user).delete()
        UserRole.objects.bulk_create([
            UserRole(user=selected_user, role_id=rid) for rid in role_ids
        ])

        messages.success(
            request,
            f"Rôles mis à jour pour {selected_user.first_name} {selected_user.last_name}."
        )
        return redirect('mainapp:attribuer_role')

    context = {
        'utilisateurs': utilisateurs,
        'roles': roles_qs,
        'selected_user': selected_user,
        'selected_role_ids': selected_role_ids,
    }
    return render(request, 'attribuer_role.html', context)

@permission_required('mainapp.add_userrole',login_url="/connexion")
@login_required(login_url="/connexion")
def attribuer_user_role(request, public_id):
    # for role in Role.objects.all():
    #     role.is_active = True
    #     role.save()
    utilisateur = get_object_or_404(User, public_id=public_id)

    roles_qs = Role.objects.filter(is_active=True).order_by('libelle')

    selected_role_ids = list(
        UserRole.objects.filter(user=utilisateur).values_list('role_id', flat=True)
    )
    roles_actuels = list(
        Role.objects.filter(id__in=selected_role_ids).values_list('libelle', flat=True)
    )

    if request.method == 'POST':
        role_ids = request.POST.getlist('roles')

        UserRole.objects.filter(user=utilisateur).delete()
        UserRole.objects.bulk_create([
            UserRole(user=utilisateur, role_id=rid) for rid in role_ids
        ])

        messages.success(
            request,
            f"Rôles mis à jour pour {utilisateur.first_name} {utilisateur.last_name}."
        )
        return redirect('mainapp:attribuer_user_role', public_id=utilisateur.public_id)

    context = {
        'utilisateur': utilisateur,
        'roles': roles_qs,
        'selected_role_ids': selected_role_ids,
        'roles_actuels': roles_actuels,
    }
    return render(request, 'attribuer_user_role.html', context)

@permission_required('mainapp.view_user',login_url="/connexion")
@login_required(login_url="/connexion")
def details_utilisateur(request, public_id):
   utilisateur = get_object_or_404(User, public_id=public_id)

   role_ids = list(
       UserRole.objects.filter(user=utilisateur).values_list('role_id', flat=True)
   )

   roles_attribues = Role.objects.filter(id__in=role_ids).order_by('libelle')

   permissions = []
   for perm in utilisateur.get_all_permissions():
       app_label, codename = perm.split(".", 1)

       permission = Permission.objects.get(
           content_type__app_label=app_label,
           codename=codename
       )

       permissions.append(permission)
   permissions_effectives = len(permissions)

   historique_recent = (
       JournalAudit.objects.filter(user=utilisateur)
       .order_by('-created')[:5]
   )

   context = {
       'utilisateur': utilisateur,
       'roles_attribues': roles_attribues,
       'permissions_effectives': permissions_effectives,
       'historique_recent': historique_recent,
   }
   return render(request, 'details_utilisateur.html', context)

@permission_required('mainapp.change_user',login_url="/connexion")
@login_required(login_url="/connexion")
def editer_utilisateur(request,public_id):
    obj = User.objects.get(public_id=public_id)
    statut = obj.is_active
    form = UserForm(instance=obj)
    if request.method == "POST":
        form = UserForm(request.POST,instance=obj)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = statut
            user.updated_by = request.user.id
            user.save()
            return redirect(reverse('mainapp:details_utilisateur',kwargs={'public_id': obj.public_id}))
        else:
            msg = get_error_message_from_form(form)
            messages.error(request, msg)
    else:
        return render(request,"editer_utilisateur.html",{"form": form})

@permission_required('mainapp.view_role',login_url="/connexion")
@login_required(login_url="/connexion")
def details_role(request, public_id):
    role = get_object_or_404(Role, public_id=public_id)

    permission_ids = set(role.permissions.values_list('id', flat=True))

    permissions_du_role = []
    for model in apps.get_app_config('mainapp').get_models():
        perms = {
            p.codename.split('_')[0]: p.id in permission_ids
            for p in Permission.objects.filter(
                content_type__app_label='mainapp',
                content_type__model=model._meta.model_name,
            )
        }
        if any(perms.values()):
            permissions_du_role.append({
                'label': model._meta.verbose_name.capitalize(),
                'view': perms.get('view', False),
                'add': perms.get('add', False),
                'change': perms.get('change', False),
                'delete': perms.get('delete', False),
            })
    permissions_du_role.sort(key=lambda m: m['label'])

    user_ids = UserRole.objects.filter(role=role).values_list('user_id', flat=True)
    utilisateurs_du_role = User.objects.filter(id__in=user_ids).order_by('last_name', 'first_name')

    context = {
        'role': role,
        'permissions_du_role': permissions_du_role,
        'utilisateurs_du_role': utilisateurs_du_role,
    }
    return render(request, 'details_role.html', context)

@permission_required('mainapp.change_role',login_url="/connexion")
@login_required(login_url="/connexion")
def modifier_role(request, public_id):
    role = get_object_or_404(Role, public_id=public_id)
    nb_utilisateurs_concernes = UserRole.objects.filter(role=role).count()

    if request.method == 'POST':
        if request.POST.get('supprimer'):
            libelle = role.libelle
            role.delete()
            messages.success(request, f"Le rôle « {libelle} » a été supprimé.")
            return redirect('mainapp:liste_roles')

        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = save_with_audit(form,request.user)
            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            messages.success(request, f"Le rôle « {role.libelle} » a été mis à jour.")
            return redirect('mainapp:details_role', public_id=role.public_id)
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = RoleForm(instance=role)

    context = {
        'form': form,
        'role': role,
        'permissions_by_model': _build_permissions_by_model(),
        'selected_permission_ids': list(role.permissions.values_list('id', flat=True)),
        'nb_utilisateurs_concernes': nb_utilisateurs_concernes,
    }
    return render(request, 'editer_role.html', context)

@permission_required('mainapp.view_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def liste_operations(request):
    return render(request,"liste_operations.html")

@permission_required('mainapp.view_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def operations_data(request):

    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    search = request.GET.get("search[value]", "")

    qs = Operation.objects.select_related(
        "client",
        "beneficiaire",
        "etablissement"
    ).order_by("-created")


    # Recherche DataTables
    if search:
        qs = qs.filter(
            Q(client__nom_client__icontains=search) |
            Q(client__prenom_client__icontains=search) |
            Q(beneficiaire__nom_client__icontains=search) |
            Q(beneficiaire__prenom_client__icontains=search) |
            Q(etablissement__libelle__icontains=search) |
            Q(etablissement__libelle__icontains=search) |
            Q(type_operation__libelle__icontains=search)
        )


    records_filtered = qs.count()

    records_total = Operation.objects.count()


    data = []

    for op in qs[start:start + length]:


        # Client
        if op.client:
            client = (
                f"{op.client.nom_client} "
                f"{op.client.prenom_client}"
            )
        else:
            client = "Non renseigné"


        # Bénéficiaire
        if op.beneficiaire:
            beneficiaire = (
                f"{op.beneficiaire.nom_client} "
                f"{op.beneficiaire.prenom_client}"
            )
        else:
            beneficiaire = "Non renseigné"

        if op.type_operation:
            type_operation = op.type_operation.libelle
        else:
            type_operation = "Non renseigné"


        # Etablissement
        if op.etablissement:
            etablissement = op.etablissement.libelle
        else:
            etablissement = "Non renseigné"


        # Date
        if op.date_ordre:
            date_operation = op.date_ordre.strftime("%d/%m/%Y")
        else:
            if op.created:
                date_operation = op.created.strftime("%d/%m/%Y")
            else:
                date_operation = ""


        data.append([
            start + len(data) + 1,
            client,
            etablissement,
            beneficiaire,
            op.nb_titre,
            type_operation,
            date_operation,
            f"""
            <a href="/donnees/operations/{op.public_id}"
               class="btn btn-icon btn-light btn-active-light-primary btn-sm"
               data-bs-toggle="tooltip"
               title="Voir les détails">

                <i class="ki-duotone ki-eye fs-4">
                    <span class="path1"></span>
                    <span class="path2"></span>
                    <span class="path3"></span>
                </i>

            </a>
            """
        ])


    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@permission_required('mainapp.add_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def effectuer_ordre(request):
    form = VenteEtTransfertForm()
    if request.method == "POST":
        form = VenteEtTransfertForm(request.POST)
        if form.is_valid():
            save_with_audit(form,request.user)
            return redirect('mainapp:home')
        else:
            messages.error(request,"Veuillez corriger les erreurs du formulaire.")
    return render(request,"saisie_ordre_bourse.html",{"form": form})

@login_required(login_url="/connexion")
def titres_par_type(request):
    type_id = request.GET.get("type_titre")
    if type_id:
        titres = Titre.objects.filter(type_titre_id=type_id).order_by("libelle")
    else:
        titres = Titre.objects.none()

    results = [{"id": t.pk, "text": str(t)} for t in titres]
    return JsonResponse({"results": results})

def clients_par_titre(request):
    titre_id = request.GET.get("titre")
    etab_id  = request.GET.get("etablissement")
    results = []
    if titre_id:
        qs = Portefeuille.objects.filter(titre_id=titre_id)
        if etab_id:
            qs = qs.filter(etablissement_id=etab_id)
        for p in qs.select_related("client"):
            results.append({
                "id": p.client_id,
                "text": str(p.client),
                "nb_titre": p.nb_titre,
            })
    return JsonResponse({"results": results})

def beneficiaires_par_etablissement(request):
    etab_id  = request.GET.get("etablissement")
    titre_id = request.GET.get("titre")
    results = []

    if etab_id:
        clients = Client.objects.filter(banque_id=etab_id)  # adapte le lien client<->etablissement

        portef = {}
        if titre_id:
            portef = dict(
                Portefeuille.objects
                .filter(etablissement_id=etab_id, titre_id=titre_id,
                        client_id__in=clients.values_list("id", flat=True))
                .values_list("client_id", "nb_titre")
            )

        for c in clients:
            nb = portef.get(c.id)                 # None si pas de portefeuille
            results.append({
                "id": c.pk,
                "text": str(c),
                "possede": nb is not None,        # booleen demande
                "nb_titre": nb if nb is not None else 0,
            })

    return JsonResponse({"results": results})

def _verrouiller_champs(form):
    form.fields["etablissement"].disabled = True
    form.fields["titre"].disabled = True
    form.fields["client"].disabled = True

    form.fields["client"].widget.attrs.pop("data-control", None)
    form.fields["client"].widget.attrs.pop("data-placeholder", None)
    form.fields["client"].widget.attrs["class"] = "form-select"


@permission_required('mainapp.add_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def achat_titres(request):

    dict_num_ordre = Operation.objects.aggregate(num_ordre=Max("num_ordre"))
    num_ordre = (dict_num_ordre["num_ordre"] or 0) + 1

    type_op_achat = TypeOperation.objects.filter(libelle="Achat de titres").first()
    type_op_vente = TypeOperation.objects.filter(libelle="Vente de titres").first()

    portefeuille_id = request.GET.get("portefeuille") or request.POST.get("portefeuille_source")

    portefeuille_source = None
    if portefeuille_id:
        portefeuille_source = Portefeuille.objects.select_related(
            "client", "titre", "etablissement"
        ).filter(pk=portefeuille_id).first()

    verrouille = bool(portefeuille_source)

    locked_initial = {}
    if verrouille:
        locked_initial = {
            "etablissement": portefeuille_source.etablissement_id,
            "titre": portefeuille_source.titre_id,
            "client": portefeuille_source.client_id,
        }

    if request.method == "POST":

        form = VenteEtTransfertForm(request.POST, initial=locked_initial)
        form.instance.type_operation = type_op_achat

        if verrouille:
            _verrouiller_champs(form)

        if form.is_valid():

            beneficiaire = form.cleaned_data["beneficiaire"]
            vendeur = form.cleaned_data["client"]
            titre = form.cleaned_data["titre"]
            nb_titre = form.cleaned_data["nb_titre"]

            try:
                with transaction.atomic():

                    portef_vendeur = Portefeuille.objects.select_for_update().get(
                        client=vendeur,
                        titre=titre
                    )

                    if portef_vendeur.nb_titre < nb_titre:
                        raise Exception("Le vendeur ne possède pas suffisamment de titres.")

                    portef_acheteur, created = Portefeuille.objects.select_for_update().get_or_create(
                        client=beneficiaire,
                        titre=titre,
                        defaults={
                            "etablissement": beneficiaire.banque,
                            "user_id": request.user.id,
                            "nb_titre": 0
                        }
                    )

                    GestionIndexTitre.vendre(
                        vendeur=vendeur,
                        acheteur=beneficiaire,
                        titre=titre,
                        quantite=nb_titre
                    )

                    portef_vendeur.nb_titre -= nb_titre
                    portef_vendeur.updated_by = request.user.id
                    portef_vendeur.save(update_fields=["nb_titre", "updated_by"])

                    portef_acheteur.nb_titre += nb_titre
                    portef_acheteur.updated_by = request.user.id
                    portef_acheteur.save(update_fields=["nb_titre", "updated_by"])

                    op = save_with_audit(form, request.user)

                    op.type_operation = type_op_achat
                    op.num_ordre = num_ordre
                    op.code_op = type_op_vente.old_id
                    op.code_op_ben = type_op_achat.old_id
                    op.date_ordre = date.today()

                    op.save()

                messages.success(request, "La vente a été effectuée avec succès.")

                return redirect(
                    reverse("mainapp:details_operation", kwargs={"public_id": op.public_id})
                )

            except Exception as e:
                messages.error(request, str(e))

        else:
            print(form.errors)
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    else:

        initial = {"num_ordre": num_ordre}

        if verrouille:
            initial.update(locked_initial)
            initial["nbportef"] = portefeuille_source.nb_titre
        else:
            # ------- Cas historique : ?vendeur=&titre= (ou accès libre) -------
            vendeur_id = request.GET.get("vendeur")
            titre_id = request.GET.get("titre")

            if vendeur_id:
                vendeur = Client.objects.filter(id=vendeur_id).first()
                if vendeur:
                    initial["client"] = vendeur.id
                    if vendeur.banque:
                        initial["etablissement"] = vendeur.banque.id

            if titre_id:
                initial["titre"] = titre_id

        form = VenteEtTransfertForm(initial=initial)

        if verrouille:
            _verrouiller_champs(form)

    return render(
        request,
        "achat_titres.html",
        {
            "form": form,
            "verrouille": verrouille,
            "portefeuille_source": portefeuille_source,
            "taux_json": json.dumps(form.get_taux_vente(), cls=DjangoJSONEncoder),
        },
    )


@permission_required('mainapp.add_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def transfert_titres(request):

    dict_num_ordre = Operation.objects.aggregate(num_ordre=Max("num_ordre"))
    num_ordre = (dict_num_ordre["num_ordre"] or 0) + 1

    type_op = TypeOperation.objects.filter(libelle='Transfert de titres').first()

    portefeuille_id = request.GET.get("portefeuille") or request.POST.get("portefeuille_source")

    portefeuille_source = None
    if portefeuille_id:
        portefeuille_source = Portefeuille.objects.select_related(
            "client", "titre", "etablissement"
        ).filter(pk=portefeuille_id).first()

    verrouille = bool(portefeuille_source)

    locked_initial = {}
    if verrouille:
        locked_initial = {
            "etablissement": portefeuille_source.etablissement_id,
            "titre": portefeuille_source.titre_id,
            "client": portefeuille_source.client_id,
        }

    if request.method == "POST":

        form = VenteEtTransfertForm(request.POST, initial=locked_initial)
        form.instance.type_operation = type_op
        form.fields["brut"].disabled = True

        if verrouille:
            _verrouiller_champs(form)

        if form.is_valid():
            beneficiaire = form.cleaned_data["beneficiaire"]
            proprio = form.cleaned_data["client"]
            titre = form.cleaned_data["titre"]
            nb_titre = form.cleaned_data["nb_titre"]

            try:
                with transaction.atomic():
                    portef_proprio = Portefeuille.objects.select_for_update().get(
                        client=proprio,
                        titre=titre
                    )

                    if portef_proprio.nb_titre < nb_titre:
                        raise Exception("Le vendeur ne possède pas suffisamment de titres.")

                    portef_benef, created = Portefeuille.objects.select_for_update().get_or_create(
                        client=beneficiaire,
                        titre=titre,
                        defaults={
                            "etablissement": beneficiaire.banque,
                            "user_id": request.user.id,
                            "nb_titre": 0
                        }
                    )

                    GestionIndexTitre.vendre(
                        vendeur=proprio,
                        acheteur=beneficiaire,
                        titre=titre,
                        quantite=nb_titre
                    )

                    portef_proprio.nb_titre -= nb_titre
                    portef_proprio.updated_by = request.user.id
                    portef_proprio.save(update_fields=["nb_titre", "updated_by"])

                    portef_benef.nb_titre += nb_titre
                    portef_benef.updated_by = request.user.id
                    portef_benef.save(update_fields=["nb_titre", "updated_by"])

                    op = save_with_audit(form, request.user)

                    op.type_operation = type_op
                    op.num_ordre = num_ordre
                    op.code_op = type_op.old_id
                    op.code_op_ben = type_op.old_id
                    op.date_ordre = date.today()

                    op.save()

                messages.success(request, "Transfert effectué avec succès.")

                # Corrigé : ancien code = redirect("mainapp:achat_titres", kwargs={...})
                return redirect(
                    reverse("mainapp:details_operation", kwargs={"public_id": op.public_id})
                )

            except Exception as e:
                messages.error(request, str(e))

        else:
            messages.error(request, "Veuillez revoir le formulaire et corriger les erreurs")

    else:

        verrouille_display = verrouille  # alias pour lisibilité côté GET

        initial = {"num_ordre": num_ordre, "brut": 0}

        if verrouille:
            initial.update(locked_initial)
            initial["nbportef"] = portefeuille_source.nb_titre

        form = VenteEtTransfertForm(initial=initial)
        form.fields["brut"].disabled = True

        if verrouille:
            _verrouiller_champs(form)

    return render(
        request,
        "transfert_titres.html",
        {
            "form": form,
            "verrouille": verrouille,
            "portefeuille_source": portefeuille_source,
            "taux_json": json.dumps(form.get_taux_vente(), cls=DjangoJSONEncoder),
        },
    )

@permission_required('mainapp.view_operation',login_url="/connexion")
@login_required(login_url="/connexion")
def details_operation(request,public_id):
    operation = Operation.objects.get(public_id=public_id)
    return render(request,"details_operation.html",{"operation": operation})


#@permission_required('mainapp.imprimer_doc',login_url="/connexion")
@login_required(login_url="/connexion")
def imprimer_attestation_titre(request, public_id):
    from urllib.parse import quote

    compte = get_object_or_404(
        Portefeuille,
        public_id=public_id
    )

    donnees_actions = compte.client.donnees_actions()

    total_actions = donnees_actions.get(
        "tot_actions"
    ) or 0

    context = {
        "client": compte.client,
        "date": date.today().strftime("%d/%m/%Y"),
        "total_actions": total_actions,
        "total_actions_lettres": nombre_en_lettres(total_actions),
        "logo_url": request.build_absolute_uri("/static/mainapp/logos/logo_AFG_Bank.png"),
    }

    html_string = render_to_string("attestation_titre.html",context)

    pdf = HTML(string=html_string,base_url=request.build_absolute_uri("/")).write_pdf()

    filename = f"attestation_titre_{compte.client.nom_client}_{compte.client.prenom_client}"

    response = HttpResponse(pdf,content_type="application/pdf")

    response["Content-Disposition"] = (
        f"inline; filename*=UTF-8''{quote(filename)}"
    )
    return response

@login_required(login_url="/connexion")
def avis_transaction(request,public_id):
    transac = get_object_or_404(Operation,public_id=public_id)
    client = transac.client
    if transac.commission:
        commission = transac.commission
    else:
        commission = 0
    if transac.tax:
        tax = transac.tax
    else:
        tax = 0
    if transac.css:
        css = transac.css
    else:
        css = 0
    if client:
        num_compte = client.num_compte
    else:
        num_compte = "-"
    total_commission = int(commission+tax+css)

    context = {

        "logo_url": request.build_absolute_uri("/static/mainapp/logos/logo_AFG_Bank.png"),

        "avis_vendeur": {

            "exemplaire": "EXEMPLAIRE VENDEUR",

            "compte": num_compte,

            "libelle_operation": "VENTE DE TITRES",

            "date": date.today(),

            "transac": transac,

            "lignes": [

                {
                    "libelle": "Nombre de titres vendus",
                    "valeur": transac.nb_titre
                },

                {
                    "libelle": "Montant brut",
                    "valeur": transac.brut
                },
                {
                    "libelle": "Cours de l'opération",
                    "valeur": transac.cours_operation
                },

                {
                    "libelle": "Commission",
                    "valeur": commission
                },
                {
                    "libelle": "TVA",
                    "valeur": tax
                },
                {
                    "libelle": "CSS",
                    "valeur": int(css)
                },
                {
                    "libelle": "TOTAL COMMISSION",
                    "valeur": total_commission
                },
                {
                    "libelle": "TTC",
                    "valeur": total_commission+transac.brut
                },

            ],

            "message":
                "Nous avons enregistré la vente de vos titres.",

        },

        "avis_client": {

            "exemplaire": "EXEMPLAIRE CLIENT",

            "client": transac.beneficiaire,

            "compte": transac.beneficiaire.num_compte,

            "libelle_operation": "ACHAT DE TITRES",

            "date": date.today(),

            "lignes": [

                {
                    "libelle": "Nombre de titres acquis",
                    "valeur": transac.nb_titre
                },

                {
                    "libelle": "Montant débité",
                    "valeur": transac.brut
                },

            ],

            "message":
                "Nous avons enregistré l'achat de vos titres.",

        },

        "client": transac.client,

    }
    html_string = render_to_string("impressions/avis_transaction.html", context)

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")

    response[
        "Content-Disposition"
    ] = (
        'inline; filename="avis_transaction.pdf"'
    )

    return response

@login_required(login_url="/connexion")
def liste_actionnaires_pdf(request):
    public_id = request.GET.get('public_id')
    titre = Titre.objects.get(public_id=public_id)
    nom_titre = titre.libelle

    portefeuilles = (
        Portefeuille.objects
        .filter(titre=titre, nb_titre__gt=0)
        .values(
            "client__nom_client",
            "client__prenom_client",
            f"client__qualite__libelle",
            "nb_titre",
        )
        .order_by("client__nom_client")
        .iterator(chunk_size=2000)
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.6 * cm,  # laisse la place au logo dessiné sur le canevas
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "TitreDoc", parent=styles["Title"], fontSize=15, alignment=TA_CENTER, leading=18,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER,
    )

    def dessiner_logo(canvas_obj, doc_obj):
        if os.path.exists(LOGO_PATH):
            logo_w, logo_h = 2.8 * cm, 1.7 * cm
            x = doc_obj.pagesize[0] - doc_obj.rightMargin - logo_w
            y = doc_obj.pagesize[1] - 2.2 * cm
            canvas_obj.drawImage(
                LOGO_PATH, x, y, width=logo_w, height=logo_h,
                preserveAspectRatio=True, mask="auto",
            )

    def dessiner_pied_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        page_num = canvas_obj.getPageNumber()
        texte = f"Page {page_num}"
        canvas_obj.drawCentredString(
            doc_obj.pagesize[0] / 2, 1 * cm, texte
        )
        canvas_obj.restoreState()

    def dessiner_page_complete(canvas_obj, doc_obj):
        dessiner_logo(canvas_obj, doc_obj)
        dessiner_pied_page(canvas_obj, doc_obj)

    story.append(Paragraph("LISTE DES ACTIONNAIRES", title_style))
    story.append(Spacer(1, 0.4 * cm))

    date_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    story.append(Paragraph(f"EN DATE DU :&nbsp;&nbsp;&nbsp;{date_str}", label_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"VALEUR :&nbsp;&nbsp;<b>{nom_titre.upper()}</b>", label_style))
    story.append(Spacer(1, 0.5 * cm))

    entetes = ["Ordre", "Qualité", "Noms ou Raison sociale", "Prénoms", "Nb Actions"]
    table_data = [entetes]

    total_actions = 0
    for i, p in enumerate(portefeuilles, start=1):
        nb = p["nb_titre"] or 0
        total_actions += nb
        table_data.append([
            str(i),
            p[f"client__qualite__libelle"] or "",
            p["client__nom_client"] or "",
            p["client__prenom_client"] or "",
            formater_nombre(nb),
        ])

    table_data.append(["", "", "", "TOTAL :", formater_nombre(total_actions)])

    col_widths = [1.5 * cm, 2.8 * cm, 6.5 * cm, 5 * cm, 2.7 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)

    doc.title = f"Liste des actionnaires de {nom_titre}"
    doc.author = "AFG Bank"
    doc.subject = "Liste des actionnaires de {nom_titre}"

    #doc.build(story, onFirstPage=dessiner_logo, onLaterPages=dessiner_logo)
    doc.build(story, onFirstPage=dessiner_page_complete, onLaterPages=dessiner_page_complete)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="liste_actionnaires.pdf"'
    return response

@login_required(login_url="/connexion")
def registre_central_pdf(request, public_id):
    buffer = construire_pdf_registre_central(public_id)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="registre_central_par_organisme.pdf"'
    return response

@login_required(login_url="/connexion")
def historique_mouvements_pdf(request, client_id, titre_id):
    client = get_object_or_404(Client, pk=client_id)
    titre = get_object_or_404(Titre, pk=titre_id)

    pdf_bytes = generer_historique_mouvements_pdf(client, titre)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    nom_fichier = f"Historique_des_mouvements_{client.nom_client}_{client.prenom_client}.pdf"
    response["Content-Disposition"] = f'inline; filename="{nom_fichier}"'
    return response

@login_required(login_url="/connexion")
def certificat_actions_pdf(request, portefeuille_id):
    portefeuille = get_object_or_404(Portefeuille, pk=portefeuille_id)

    pdf_bytes = generer_certificat_actions_pdf(portefeuille)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    nom_fichier = f"Certificat_actions_{portefeuille.client.pk}_{portefeuille.titre.pk}.pdf"
    response["Content-Disposition"] = f'inline; filename="{nom_fichier}"'
    return response

@login_required(login_url="/connexion")
def avis_transaction_achat_vente_pdf(request, public_id):
    operation = get_object_or_404(Operation, public_id=public_id)

    vendeur_ctx, acheteur_ctx = build_contexts_from_operation(operation)

    buffer = io.BytesIO()
    generate_avis_pdf(vendeur_ctx, acheteur_ctx, buffer)
    buffer.seek(0)

    filename = f"avis_transaction_{operation.num_ordre}.pdf"

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=filename,
        content_type="application/pdf",
    )

def ajouter_portefeuille(request, public_id):

    client = get_object_or_404(Client, public_id=public_id)

    if request.method == "POST":

        form = PortefeuilleForm(request.POST)
        form.instance.client = client
        form.instance.nb_titre = 0

        if form.is_valid():
            deja_existant = Portefeuille.objects.filter(
                client=client,
                titre=form.cleaned_data["titre"],
                etablissement=form.cleaned_data["etablissement"],
            ).exists()

            if deja_existant:
                messages.error(
                    request,
                    "Un portefeuille existe déjà pour ce client, ce titre et cet établissement."
                )
            else:
                save_with_audit(form, request.user)
                messages.success(request, "Le portefeuille a été créé avec succès.")

        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    return redirect(
        reverse("mainapp:details_souscripteur", kwargs={"public_id": client.public_id})
    )


@permission_required('mainapp.valider_operation', raise_exception=True)
@login_required(login_url="/connexion")
def valider_operation(request, public_id):
    operation = get_object_or_404(Operation, public_id=public_id)

    if operation.est_valide:
        messages.warning(request, "Cette opération est déjà validée.")
        return redirect('mainapp:detail_operation', public_id=operation.public_id)

    if request.method == 'POST':
        operation.est_valide = True
        operation.nom_modif = f"{request.user.first_name} {request.user.last_name}"
        operation.date_modif = timezone.now().date()
        operation.save()

        messages.success(
            request,
            f"L'ordre N°{operation.num_ordre} a été validé avec succès."
        )
        return redirect('mainapp:detail_operation', public_id=operation.public_id)

    return redirect('mainapp:detail_operation', public_id=operation.public_id)




    




