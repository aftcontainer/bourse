from django.urls import path
from . import views

app_name = "mainapp"

urlpatterns = [
    path('login', views.sign_in,name="sign_in"),
    path('', views.home,name="home"),
    path('donnees', views.donnees,name="donnees"),
    path('impressions', views.impressions,name="impressions"),
    path('parametres', views.parametres,name="parametres"),
    path('parametres/devises', views.liste_devises,name="liste_devises"),
    path('parametres/qualites', views.liste_qualites,name="liste_qualites"),
    path('parametres/categories-clients', views.liste_categories_clients,name="liste_cat_clients"),
    path('parametres/types-operations', views.liste_t_operations,name="liste_t_operations"),
    path('parametres/creer-types-operations', views.creer_t_operation,name="creer_t_operation"),
    path('parametres/types-operations/<uuid:public_id>/editer', views.editer_t_operation,name="editer_t_operation"),
    path('parametres/types-operations/<uuid:public_id>', views.details_t_operation,name="details_t_operation"),
    path('parametres/types-titres', views.liste_t_titres,name="liste_t_titres"),
    path('parametres/titres', views.liste_titres,name="liste_titres"),
    path('parametres/creer-titre', views.creer_titre,name="creer_titre"),
    path('parametres/titre/<uuid:public_id>/editer', views.editer_titre,name="editer_titre"),
    path('parametres/titre/<uuid:public_id>', views.details_titre,name="details_titre"),
    path('donnees/etablissements', views.liste_ets,name="liste_ets"),
    path('donnees/etablissements/<uuid:public_id>', views.details_ets,name="details_ets"),
    path('donnees/etablissements/<uuid:public_id>/editer', views.editer_ets,name="editer_ets"),
    path('donnees/etablissements/creer', views.creer_ets,name="creer_ets"),
    path('donnees/souscripteurs', views.liste_clients,name="liste_clients"),
    path('utilisateurs', views.gestion_utilisateurs,name="gestion_utilisateurs"),
    path('utilisateurs/liste', views.liste_utlisateurs,name="liste_utlisateurs"),
    path('utilisateurs/nouveau', views.creer_utilisateur,name="creer_utilisateur"),
    path('utilisateurs/<uuid:public_id>/editer', views.editer_utilisateur,name="editer_utilisateur"),
    path('donnees/souscripteurs', views.liste_clients,name="liste_clients"),
    path('donnees/souscripteurs/creer', views.creer_souscripteur,name="creer_souscripteur"),
    path('donnees/souscripteurs/<uuid:public_id>/editer', views.creer_souscripteur,name="creer_souscripteur"),
]