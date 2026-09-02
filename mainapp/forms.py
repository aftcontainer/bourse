import datetime
import os
import smtplib
import logging

from django import forms
from django.template import loader
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.safestring import mark_safe

from mainapp.models import Devise, Pays, TypePiece, TypeOperation, CategorieClient, Qualite, TypeTitre, Client, \
    Titre, Operation, Etablissement, Ville, User, CategorieAction, Role, Portefeuille

UserModel = get_user_model()
logger = logging.getLogger("django.contrib.auth")
from email.message import EmailMessage

from decimal import Decimal, ROUND_HALF_UP

err_msg = {
    "required": "Ce champ est obligatoire",
    "invalid": "Veuillez saisir une adresse email correcte !"
}

CTRL   = "form-control"
NUM    = "form-control num-input"
CALC   = "form-control num-input is-computed"
SELECT = "form-select"
SELECT2 = "form-select"

SENS_CHOICES = [
    ("", "---------"),
    ("V", "Vente de titres"),
    ("A", "Achat de titres"),
    ("T", "Transfert de titres")
]

OP_BEN_CHOICES = [
    ("", "---------"),
    (1, "Achat de titres"),
    (2, "Vente de titres"),
]




class DeviseForm(forms.ModelForm):

    class Meta:
        model = Devise
        fields = '__all__'
        widgets = {
            'code_devise': forms.TextInput(attrs={'class': 'form-control form-control-solid text-uppercase', 'placeholder': 'Code'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'})
        }


class PaysForm(forms.ModelForm):

    class Meta:
        model = Pays
        fields = '__all__'


class TypePieceForm(forms.ModelForm):

    class Meta:
        model = TypePiece
        fields = '__all__'

class TypeOperationForm(forms.ModelForm):

    SENS_CHOICES = [
        ('D', 'Débit'),
        ('C', 'Crédit'),
    ]

    mvnt_operation = forms.ChoiceField(
        choices=SENS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-solid'}),
        label='Sens',
    )

    class Meta:
        model = TypeOperation
        fields = '__all__'
        widgets = {
            'old_id': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Code'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'}),
            'commission': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Taux commission', 'step': '0.00001'}),
            'rcm': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Taux IRCM', 'step': '0.00001'}),
            'tva': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Taux TVA', 'step': '0.00001'}),
            'css': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Taux CSS', 'step': '0.00001'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        champs_obligatoires = ['old_id', 'libelle', 'commission', 'rcm', 'tva', 'css']
        for name in champs_obligatoires:
            self.fields[name].required = True

class CategorieClientForm(forms.ModelForm):

    class Meta:
        model = CategorieClient
        fields = '__all__'
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'})
        }


class QualiteForm(forms.ModelForm):

    class Meta:
        model = Qualite
        fields = '__all__'
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'})
        }


class TypeTitreForm(forms.ModelForm):

    class Meta:
        model = TypeTitre
        fields = '__all__'
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'})
        }


class ClientForm(forms.ModelForm):
    category_client = forms.ModelChoiceField(
        queryset=CategorieClient.objects.order_by('libelle'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )
    banque = forms.ModelChoiceField(
        queryset=Etablissement.objects.order_by('libelle'),
        required=False, empty_label="— Choisir —",
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )
    qualite = forms.ModelChoiceField(
        queryset=Qualite.objects.all(),
        required=False, empty_label="— Choisir —",
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )
    pays = forms.ModelChoiceField(
        queryset=Pays.objects.order_by('nom_pays'),
        required=False, empty_label="— Choisir —",
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )
    type_piece = forms.ModelChoiceField(
        queryset=TypePiece.objects.all(),
        required=False, empty_label="— Choisir —",
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )
    exonerer_taxe = forms.ChoiceField(
        choices=[('', '— Choisir —'), ('OUI', 'Oui'), ('NON', 'Non')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )

    ca_code = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ca_code'].choices = [('', '— Choisir —')] + [
            (c.code_cat, c.libelle_cat)
            for c in CategorieAction.objects.order_by('libelle_cat')
        ]

    class Meta:
        model = Client
        fields = [
            "banque", "indentifiant", "num_compte", "matricule",
            "category_client", "ca_code",
            "qualite", "nom_client", "prenom_client",
            "date_naissance", "lieu_naissance", "pays",
            "type_piece", "num_carte", "nature_carte",
            "adresse", "ville", "bp_client",
            "tel_client", "fax_client", "email_client", "site_client",
            "tx_commission", "exonerer_taxe",
        ]
        widgets = {
            'indentifiant': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'num_compte': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Numéro de compte espèces'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Matricule salarié'}),
            'nom_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Nom ou Raison sociale'}),
            'prenom_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Prénoms'}),
            'date_naissance': forms.DateInput(
                attrs={'class': 'form-control form-control-solid', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Lieu de naissance'}),
            'num_carte': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': "Numéro de pièce d'identité"}),
            'nature_carte': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Nature de la carte'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Adresse'}),
            'ville': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Résidence / Ville'}),
            'bp_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Boîte postale'}),
            'tel_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Téléphone'}),
            'fax_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Fax'}),
            'email_client': forms.EmailInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Email'}),
            'site_client': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Site web'}),
            'tx_commission': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'step': '0.01'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'step': '0.01'}),
        }


class TitreForm(forms.ModelForm):
    devise = forms.ModelChoiceField(
        queryset=Devise.objects.order_by('libelle').order_by('libelle'), required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )

    type_titre = forms.ModelChoiceField(
        queryset=TypeTitre.objects.order_by('libelle').order_by('libelle'), required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )

    class Meta:
        model = Titre
        fields = '__all__'
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'Libellé'}),
            'nominal': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'nominal': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'cours': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'cours_oblig': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'dercoupon': forms.DateInput(attrs={'class': 'form-control form-control-solid'}),
            'nb_actions': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'nb_mini': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'tx_oblig': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
        }

class UserForm(forms.ModelForm):
    ROLE_OPERATEUR = 'Opérateur'
    ROLE_ADMINISTRATEUR = 'Administrateur'

    ROLE_CHOICES = [
        (ROLE_OPERATEUR, 'Opérateur'),
        (ROLE_ADMINISTRATEUR, 'Administrateur'),
    ]

    class Meta:
        model = User
        fields = '__all__'
        exclude = ["password"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-solid'}),
            'username': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'role': forms.Select(attrs={'class': 'form-control form-control-solid'})

        }


class OperationForm(forms.ModelForm):

    class Meta:
        model = Operation
        fields = '__all__'

class EtablissementForm(forms.ModelForm):
    ville = forms.ModelChoiceField(
        queryset=Ville.objects.order_by('nom_ville').order_by('nom_ville'), required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-solid'})
    )

    class Meta:
        model = Etablissement
        fields = '__all__'

        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'bp_etablissement': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'type_com': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'min_commission': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'tx_retro': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'min_retro': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'plafond_commission': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'tx_commission': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'plafond_commission2': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'tx_commission2': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'tx_commission3': forms.NumberInput(attrs={'class': 'form-control form-control-solid'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

class PortefeuilleForm(forms.ModelForm):
    class Meta:
        model = Portefeuille
        fields = ["etablissement", "titre"]
        widgets = {
            "etablissement": forms.Select(attrs={
                "class": "form-select form-select-solid",
                "data-control": "select2",
            }),
            "titre": forms.Select(attrs={
                "class": "form-select form-select-solid",
            }),
        }
        labels = {
            "etablissement": "Établissement",
            "titre": "Titre",
        }

class SignInForm(forms.Form):
    email = forms.EmailField(
        max_length=70,required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Nom d\'utilisateur'})
    )
    password  = forms.CharField(
        max_length=200,required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe','name': 'user_password',
            'class': 'form-control'
        })
    )

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['libelle', 'description', 'is_active']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VenteEtTransfertForm(forms.ModelForm):
    OPERATION_LIBELLE = "Achat de titres"
    OPERATION_LIBELLE2 = "Transfert de titres"
    type_operation = forms.ModelChoiceField(queryset=TypeOperation.objects.order_by('libelle'),required=False)

    class Meta:
        model = Operation
        fields = [
            "etablissement", "titre",
            "client", "beneficiaire",
            "nbportef", "cours_operation", "nb_titre", "nbencours",
            "brut", "montant", "commission", "tax", "css", "ircm",
            "nbportefben","num_ordre","num_seq_ordre","code_op",
            "etablissement_ben","tot_nbportebef",'type_operation'
        ]
        read_only_fields = ['ircm']
        widgets = {
            "etablissement": forms.Select(attrs={"class": SELECT2, "data-control": "select2"}),
            "titre": forms.Select(attrs={"class": SELECT, "id": "id_titre"}),
            "date_ordre": forms.DateInput(attrs={"class": CTRL, "type": "date"}),

            "client": forms.Select(attrs={"class": SELECT2, "data-control": "select2","data-placeholder": "Rechercher un client..."}),

            "nbportef": forms.NumberInput(attrs={"class": CALC, "readonly": True}),
            "cours_operation": forms.NumberInput(attrs={"class": NUM,"min": 10000}),
            "nb_titre": forms.NumberInput(attrs={"class": NUM}),
            "nbencours": forms.NumberInput(attrs={"class": CALC, "readonly": True}),
            "tot_nbportebef": forms.NumberInput(attrs={"class": CALC, "readonly": True}),

            "brut": forms.NumberInput(attrs={"class": CALC, "readonly": True}),
            "montant": forms.NumberInput(attrs={"class": CALC, "readonly": True}),
            "commission": forms.NumberInput(attrs={"class": NUM,"readonly": True}),
            "tax": forms.NumberInput(attrs={"class": NUM,"readonly": True}),
            "css": forms.NumberInput(attrs={"class": NUM,"readonly": True, "step": "0.01","min": "0"}),
            "ircm": forms.NumberInput(attrs={"class": NUM}),

            "beneficiaire": forms.Select(attrs={"class": SELECT2, "data-control": "select2","data-placeholder": "Rechercher un beneficiaire..."}),
            "nbportefben": forms.NumberInput(attrs={"class": CALC, "readonly": True}),
            "etablissement_ben": forms.Select(attrs={"class": SELECT2, "data-control": "select2"}),

            "num_ordre": forms.HiddenInput(),
            "num_seq_ordre": forms.HiddenInput(),
            "code_op": forms.HiddenInput(),
        }
        labels = {
            "etablissement": "Donneur d'ordre",
            "etablissement_ben": "Donneur d'ordre",
            "titre": "Titre",
            "client": "Vendeur",
            "beneficiaire": "Beneficiaire",
            "nbportef": "Titres en portefeuille",
            "cours_operation": "Cours de cession",
            "nb_titre": "Nombre de titres en transaction",
            "nbencours": "Nombre total de titres",
            "tot_nbportebef": "Nombre total de titres",
            "brut": "Montant brut",
            "montant": "Débit compte client",
            "commission": "Montant commission (1%)",
            "tax": "Montant TVA (18%)",
            "css": "Montant CSS",
            "ircm": "Montant IRCM",
            "nbportefben": "Titres en portefeuille (beneficiaire)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["titre"].queryset = Titre.objects.all()
        self.fields["client"].queryset = Client.objects.none()
        self.fields["beneficiaire"].queryset = Client.objects.none()

        self.initial['cours_operation'] = 10000

        titre_id = self._val("titre")
        etab_id = self._val("etablissement")
        etab_ben_id = self._val("etablissement_ben")

        if etab_id and titre_id:
            self.fields["client"].queryset = Client.objects.filter(
                portefeuille__etablissement_id=etab_id,
                portefeuille__titre_id=titre_id,
            ).distinct()

        if etab_ben_id and titre_id:
            self.fields["beneficiaire"].queryset = Client.objects.filter(
                banque_id=etab_ben_id
            ).distinct()

    def _val(self, name):
        if name in self.data:
            try:
                return int(self.data.get(name))
            except (TypeError, ValueError):
                return None
        # NOUVEAU : on tient compte des valeurs passées via initial=
        # (cas de l'arrivée depuis la page détail du portefeuille)
        if self.initial.get(name):
            try:
                val = self.initial.get(name)
                return val.pk if hasattr(val, "pk") else int(val)
            except (TypeError, ValueError):
                return None
        return getattr(self.instance, name + "_id", None)

    def clean(self):
        cleaned = super().clean()
        cours = cleaned.get("cours_operation")
        type_operation = cleaned.get("type_operation") or self.instance.type_operation
        nb = cleaned.get("nb_titre")
        portef = cleaned.get("nbportef")

        if cours is not None and cours < 10000:
            self.add_error("cours_operation", "Le cours de cession ne doit pas être inférieur à 10 000.")

        if portef is not None and nb is not None:
            if portef - nb < 0:
                self.add_error("nb_titre","Les titres en transaction (%d) dépassent le portefeuille (%d)." % (nb, portef))
            else:
                cleaned["nbencours"] = portef - nb

        if cours and nb:
            if type_operation.libelle in ("Achat de titres", "Vente de titres"):
                taux = self.get_taux_vente()
            elif type_operation.libelle == 'Transfert de titres':
                taux = self.get_taux_transfert()
            brut = cours * nb
            commission = (brut * taux["commission"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            tva = (commission * taux["tva"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ircm = (commission * taux["ircm"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            css = (commission * taux["css"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            net = (brut + commission + tva + ircm + css).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

            cleaned["brut"] = brut
            cleaned["commission"] = commission
            cleaned["tax"] = tva
            cleaned["ircm"] = ircm
            cleaned["css"] = css
            cleaned["montant"] = net

        return cleaned

    def get_taux_vente(self):
        op = TypeOperation.objects.filter(libelle=self.OPERATION_LIBELLE).first()
        defaut = {"commission": 0.01, "tva": 0.18, "ircm": 0.0, "css": 0.01}
        if not op:
            return defaut

        def frac(v):
            return Decimal(v) / Decimal(100) if v is not None else Decimal("0.0")

        return {
            "commission": frac(op.commission),
            "tva": frac(op.tva),
            "ircm": frac(op.rcm),
            "css": frac(op.css),
        }

    def get_taux_transfert(self):
        op = TypeOperation.objects.filter(libelle=self.OPERATION_LIBELLE2).last()
        defaut = {"commission": 0.00, "tva": 0.0, "ircm": 0.0, "css": 0.0}
        if not op:
            return defaut
        def frac(v):
            return Decimal(v) / Decimal(100) if v is not None else Decimal("0.0")

        return {
            "commission": frac(op.commission),
            "tva": frac(op.tva),
            "ircm": frac(op.rcm),
            "css": frac(op.css),
        }

class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,):

        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        try:
            msg = EmailMessage()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.add_alternative(body, subtype='html')

            logger.info(f"Log: {from_email} envoyé")

            with smtplib.SMTP(os.environ.get('SMTP_SERVER'), int(os.environ.get('SMTP_PORT'))) as server:
                server.starttls()
                server.login(os.environ.get('SENDER_EMAIL'), os.environ.get('EMAIL_PASSWORD'))
                server.send_message(msg)

                server.send_message(msg)
                logger.info(f"Email envoyé avec succès.")
        except:
            logger.exception(
                "Failed to send password reset email to %s", context["user"].pk
            )


    def save(self,domain_override=None,subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            user_email = getattr(user, email_field_name)
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
            )

class ResetEmailForm(forms.Form):
    email = forms.EmailField(
        max_length=70, error_messages=err_msg,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )

class SetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": "Les mots de passes ne sont pas identiques.",
    }
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "Nouveau mot de passe", "class": "form-control"}),
        strip=False,
        help_text=mark_safe(
            """
                <ul>
                    <li>Au moins 8 caractères.</li>
                    <li>Eviter les infos personnelles</li>
                    <li>Ne doit pas être un mot de passe courant.</li>
                    <li>Ne doit pas être composé uniquement de chiffres.</li>
                </ul>
            """
        ),
    )
    new_password2 = forms.CharField(
        label= "Confirmation de mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "Nouveau mot de passe", "class": "form-control"}),
    )



