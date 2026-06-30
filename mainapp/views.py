import oracledb
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
import secrets

from mainapp.forms import SignInForm, DeviseForm, QualiteForm, CategorieClientForm, TypeOperationForm, TypeTitreForm, \
    TitreForm, EtablissementForm, UserForm, ClientForm
from .models import Devise, Qualite, CategorieClient, TypeOperation, TypeTitre, Titre, Etablissement, Client,User

from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages

from .utils import is_ajax, get_error_message_from_form

# connection1 = oracledb.connect(
#     user="BOURUSER",
#     password="Afri2012",
#     host="192.168.1.102",
#     port=1521,
#     service_name="BOURSE"
# )

def sign_in(request):
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
                    return render(request, "mainapp/sign_in.html", {"form": form})
            else:
                messages.add_message(request, messages.ERROR, "Login ou mot de passe inconnu")
                return render(request, "mainapp/sign_in.html", {"form": form})
        else:
            messages.add_message(request, messages.WARNING, "Veuillez vérifier les informations et continuer.")
            return render(request, "mainapp/sign_in.html", {"form": form})
    return render(request,"login.html",{"form": form})


def home(request):
    return render(request, "base.html")

def donnees(request):
    return render(request,"donnees.html")

def impressions(request):
    return render(request,"impressions.html")

def parametres(request):
    return render(request,"parametres.html")

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

def details_t_operation(request,public_id):
    obj = TypeOperation.objects.get(public_id=public_id)
    return render(request, "details_t_operation.html", {"obj": obj})

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

def liste_titres(request):
    titres = Titre.objects.all().order_by('libelle')
    return render(request,"liste_titres.html",{"titres": titres})

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

def details_titre(request,public_id):
    obj = Titre.objects.get(public_id=public_id)
    return render(request,"details_titre.html",{"obj": obj})


def liste_ets(request):
    ets = Etablissement.objects.all().order_by('libelle')
    return render(request,"liste_ets.html",{"ets": ets})

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

def details_ets(request,public_id):
    obj = Etablissement.objects.get(public_id=public_id)
    return render(request,"details_ets.html",{"obj": obj})

def liste_clients(request):
    clients = Client.objects.all()
    return render(request,"liste_clients",{"clients": clients})

def gestion_utilisateurs(request):
    return render(request,"gestion_users.html")

def liste_utlisateurs(request):
    users = User.objects.all().order_by('last_name')
    return render(request,"liste_users.html",{"users": users})


def creer_utilisateur(request):
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = secrets.token_urlsafe(8)
            user.save()
            print("***********************")
            print(user.password)
            print("***********************")
            return render(request,"liste_users.html")
        else:
            msg = get_error_message_from_form(form)
            messages.add_message(request, messages.WARNING,msg)
            return render(request, "creer_utilisateur.html", {"form": form})
    else:
        return render(request, "creer_utilisateur.html", {"form": form})

def editer_utilisateur(request,public_id):
    obj = User.objects.get(public_id=public_id)
    form = UserForm(instance=obj)
    if request.method == "POST":
        form = UserForm(request.POST,instance=obj)
        if form.is_valid():
            form.save()
            return render(request,"liste_users.html")
        else:
            msg = get_error_message_from_form(form)
            messages.add_message(request, messages.WARNING, msg)
            return render(request,"editer_utilisateur.html", {"form": form})
    else:
        return render(request, "editer_utilisateur.html", {"form": form})

def liste_clients(request):
    clients = Client.objects.all()
    return render(request,"liste_clients.html",{"clients": clients})

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












