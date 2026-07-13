import oracledb
import json
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import Permission
from django.core.paginator import Paginator
from django.db.models import Max
from django.http import JsonResponse, HttpResponse
import secrets

from django.utils.http import urlsafe_base64_decode

from mainapp.forms import SignInForm, DeviseForm, QualiteForm, CategorieClientForm, TypeOperationForm, TypeTitreForm, \
    TitreForm, EtablissementForm, UserForm, ClientForm, RoleForm, VenteEtTransfertForm
from .models import Devise, Qualite, CategorieClient, TypeOperation, TypeTitre, Titre, Etablissement, Client, User, \
    Portefeuille, Role, JournalAudit, UserRole, Operation

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages

from .utils import is_ajax, get_error_message_from_form

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .tasks import email_activation_compte

# connection1 = oracledb.connect(
#     user="BOURUSER",
#     password="Afri2012",
#     host="192.168.1.102",
#     port=1521,
#     service_name="BOURSE"
# )

def se_connecter(request):
    form = SignInForm()
    if request.method == "POST":
        form = SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(email=email, password=password)
            print(f"{user} authentifié...")
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
    operations = Operation.objects.all()[:5]
    return render(
        request, "home.html",
        {
            "nb_titres":nb_titres,
            "nb_operations": nb_operations,
            "nb_clients": nb_clients,
            "operations": operations
         }
    )

@login_required(login_url="/connexion")
def donnees(request):
    return render(request,"donnees.html")

@login_required(login_url="/connexion")
def impressions(request):
    return render(request,"impressions.html")

@login_required(login_url="/connexion")
def parametres(request):
    return render(request,"parametres.html")

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
                form.save()
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_devises.html", {"devises": devises})

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
                form.save()
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_qualites.html", {"qualites": qualites})

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
                form.save()
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_cat_clients.html", {"cats": cats})

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

@login_required(login_url="/connexion")
def creer_t_operation(request):
    form = TypeOperationForm()
    if request.method == "POST":
        form = TypeOperationForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return redirect(reverse('mainapp:details_t_operation',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "erreur")
            return render(request,"creer_t_operation.html",{"form": form})
    return render(request,"creer_t_operation.html",{"form": form})

@login_required(login_url="/connexion")
def editer_t_operation(request,public_id):
    obj = TypeOperation.objects.get(public_id=public_id)
    form = TypeOperationForm(instance=obj)
    if request.method == "POST":
        form = TypeOperationForm(request.POST,instance=obj)
        if form.is_valid():
            form.save()
            return redirect(reverse('mainapp:details_t_operation',kwargs={'public_id':obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "editer_t_operation.html", {"form": form,"obj": obj})
    return render(request, "editer_t_operation.html", {"form": form,"obj": obj})

@login_required(login_url="/connexion")
def details_t_operation(request,public_id):
    obj = TypeOperation.objects.get(public_id=public_id)
    return render(request, "details_t_operation.html", {"obj": obj})

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
                form.save()
                return JsonResponse({"msg": msg,"status": "success"})
            except:
                return JsonResponse({"msg": "Une erreur s'est produite","status": "error"})
        else:
            msg = get_error_message_from_form(form)
            return JsonResponse({"msg": msg, "status": "warning"})
    return render(request, "liste_t_titres.html", {"t_titres": t_titres})

@login_required(login_url="/connexion")
def liste_titres(request):
    titres = Titre.objects.all().order_by('libelle')
    return render(request,"liste_titres.html",{"titres": titres})

@login_required(login_url="/connexion")
def creer_titre(request):
    form = TitreForm()
    if request.method == "POST":
        form = TitreForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return redirect(reverse('mainapp:details_titre',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "creer_titre.html", {"form": form})
    else:
        return render(request, "creer_titre.html", {"form": form})

@login_required(login_url="/connexion")
def editer_titre(request,public_id):
    obj = Titre.objects.get(public_id=public_id)
    form = TitreForm(instance=obj)
    if request.method == "POST":
        form = TitreForm(request.POST,instance=obj)
        if form.is_valid():
            form.save()
            return redirect(reverse('mainapp:liste_titres'))
        messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
        return render(request, "editer_titre.html", {"form": form,"obj": obj})
    return render(request, "editer_titre.html", {"form": form, "obj": obj})

@login_required(login_url="/connexion")
def details_titre(request,public_id):
    obj = Titre.objects.get(public_id=public_id)
    return render(request,"details_titre.html",{"obj": obj})

@login_required(login_url="/connexion")
def liste_ets(request):
    ets = Etablissement.objects.all().order_by('libelle')
    return render(request,"liste_ets.html",{"ets": ets})

@login_required(login_url="/connexion")
def creer_ets(request):
    form = EtablissementForm()
    if request.method == "POST":
        form = EtablissementForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return redirect(reverse('mainapp:details_ets',kwargs={'public_id':obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "creer_ets.html", {"form": form})
    return render(request, "creer_ets.html", {"form": form})

@login_required(login_url="/connexion")
def editer_ets(request,public_id):
    obj = Etablissement.objects.get(public_id=public_id)
    form = EtablissementForm(instance=obj)
    if request.method == "POST":
        form = EtablissementForm(request.POST,instance=obj)
        if form.is_valid():
            form.save()
            return redirect(reverse('mainapp:details_ets',kwargs={'public_id': obj.public_id}))
        else:
            messages.add_message(request, messages.WARNING, "Verifiez les informations et réessayez.")
            return render(request, "editer_ets.html", {"form": form})
    return render(request, "editer_ets.html", {"form": form})

@login_required(login_url="/connexion")
def details_ets(request,public_id):
    obj = Etablissement.objects.get(public_id=public_id)
    return render(request,"details_ets.html",{"obj": obj})

@login_required(login_url="/connexion")
def gestion_utilisateurs(request):
    return render(request,"gestion_users.html")

@login_required(login_url="/connexion")
def liste_utilisateurs(request):
    users = User.objects.all().order_by('last_name')
    return render(request,"liste_users.html",{"users": users})

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

@login_required(login_url="/connexion")
def liste_clients(request):
    clients = Client.objects.all()
    return render(request,"liste_clients.html",{"clients": clients})

@login_required(login_url="/connexion")
def creer_souscripteur(request):
    form = ClientForm()
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request,"liste_clients.html",{"clients": Client.objects.all()})
        else:
            msg = get_error_message_from_form(form)
            messages.add_message(request, messages.WARNING, msg)
            return render(request, "creer_souscripteur.html", {"form": form})
    else:
        return render(request, "creer_souscripteur.html", {"form": form})

@login_required(login_url="/connexion")
def editer_souscripteur(request,public_id):
    obj = Client.objects.get(public_id=public_id)
    form = ClientForm(instance=obj)
    if request.method == "POST":
        form = ClientForm(request.POST,instance=obj)
        if form.is_valid():
            obj = form.save()
            return redirect(reverse('mainapp:details_souscripteur',kwargs={'public_id':obj.public_id}))
        msg = get_error_message_from_form(form)
        messages.add_message(request, messages.WARNING, msg)
        return render(request, "editer_souscripteur.html", {"form": form})
    return render(request, "editer_souscripteur.html", {"form": form})

@login_required(login_url="/connexion")
def details_souscripteur(request,public_id):
    obj = Client.objects.get(public_id=public_id)
    return render(request,"details_souscripteur.html",{"obj": obj})

@login_required(login_url="/connexion")
def liste_comptes(request):
    comptes = Portefeuille.objects.all()
    return render(request,"liste_comptes.html",{"comptes": comptes})

@login_required(login_url="/connexion")
def liste_roles(request):
    roles = Role.objects.all().order_by("libelle")
    return render(request,"liste_roles.html",{"roles": roles})

def _build_permissions_by_model(selected_ids=None):
    """Construit la matrice module -> {view, add, change, delete}."""
    selected_ids = selected_ids or []
    app_models = apps.get_app_config('mainapp').get_models()

    permissions_by_model = []
    for model in app_models:
        ct = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(content_type=ct)
        perms_map = {p.codename.split('_')[0]: p for p in perms}
        permissions_by_model.append({
            'label': model._meta.verbose_name.capitalize(),
            'model_name': model._meta.model_name,
            'perms': perms_map,
        })

    permissions_by_model.sort(key=lambda m: m['label'])
    return permissions_by_model

@login_required(login_url="/connexion")
def creer_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()

            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            role.is_active = True
            role.save()
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

@login_required(login_url="/connexion")
def editer_role(request, public_id):
    role = get_object_or_404(Role, public_id=public_id)

    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
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

@login_required(login_url="/connexion")
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

    context = {
        'logs': logs,
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

@login_required(login_url="/connexion")
def attribuer_role(request):
    utilisateurs_qs = User.objects.all().order_by('last_name', 'first_name')
    roles_qs = Role.objects.filter(is_active=True).order_by('libelle')

    # Pré-calcule les rôles de chaque utilisateur pour l'affichage
    # (tableau récapitulatif + attribut data-roles du <select>)
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

@login_required(login_url="/connexion")
def attribuer_user_role(request, public_id):
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

def details_utilisateur(request, public_id):
   utilisateur = get_object_or_404(User, public_id=public_id)

   role_ids = list(
       UserRole.objects.filter(user=utilisateur).values_list('role_id', flat=True)
   )
   roles_attribues = Role.objects.filter(id__in=role_ids).order_by('libelle')
   from django.apps import apps
   from django.contrib.contenttypes.models import ContentType

   permission_ids = set(
       Role.objects.filter(id__in=role_ids)
       .values_list('permissions__id', flat=True)
   )

   permissions_effectives = []
   for model in apps.get_app_config('mainapp').get_models():
       ct = ContentType.objects.get_for_model(model)
       perms = {
           p.codename.split('_')[0]: p.id in permission_ids
           for p in Permission.objects.filter(content_type=ct)
       }
       if any(perms.values()):
           permissions_effectives.append({
               'label': model._meta.verbose_name.capitalize(),
               'view': perms.get('view', False),
               'add': perms.get('add', False),
               'change': perms.get('change', False),
               'delete': perms.get('delete', False),
           })
   permissions_effectives.sort(key=lambda m: m['label'])

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
            user.save()
            return redirect(reverse('mainapp:details_utilisateur',kwargs={'public_id': obj.public_id}))
        else:
            msg = get_error_message_from_form(form)
            messages.error(request, msg)
    else:
        return render(request,"editer_utilisateur.html",{"form": form})

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
            role = form.save()
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

@login_required(login_url="/connexion")
def liste_operations(request):
    ordres = Operation.objects.all()
    return render(request,"liste_operations.html",{"ordres": ordres})

@login_required(login_url="/connexion")
def effectuer_ordre(request):
    form = VenteEtTransfertForm()
    if request.method == "POST":
        form = VenteEtTransfertForm(request.POST)
        if form.is_valid():
            form.save()
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

from django.http import JsonResponse
from .models import Portefeuille

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

def achat_titres(request):
    dict_num_ordre = Operation.objects.aggregate(num_ordre=Max('num_ordre'))
    num_ordre = dict_num_ordre['num_ordre'] + 1

    initial = {'num_ordre': num_ordre,'type_op': 1}
    form = VenteEtTransfertForm(initial=initial)
    if request.method == "POST":
        form = VenteEtTransfertForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
            messages.error(request,"Veuillez revoir le formulaire et corriger les erreurs")
            return render(request,"achat_titres.html",{"form": form})
    return render(request,"achat_titres.html",{"form": form,"taux_json": json.dumps(form.get_taux_vente()),})

def beneficiaires_par_etablissement(request):
    etab_id  = request.GET.get("etablissement")
    titre_id = request.GET.get("titre")
    results = []

    if etab_id:
        clients = Client.objects.filter(banque_id=etab_id)  # adapte le lien client<->etablissement

        # Portefeuilles de ces clients pour CE titre -> dict {client_id: nb_titre}
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

def transfert_titres(request):
    dict_num_ordre = Operation.objects.aggregate(num_ordre=Max('num_ordre'))
    num_ordre = dict_num_ordre['num_ordre'] + 1

    initial = {'num_ordre': num_ordre, 'type_op': 2}
    form = VenteEtTransfertForm(initial=initial)
    if request.method == "POST":
        form = VenteEtTransfertForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            messages.error(request,"Veuillez revoir le formulaire et corriger les erreurs")
    return render(request,"transfert_titres.html",{"form": form,"taux_json": json.dumps(form.get_taux_transfert()),})

    




