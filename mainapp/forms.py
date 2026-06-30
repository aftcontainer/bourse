from django import forms

from mainapp.models import Devise, Pays, TypePiece, TypeOperation, CategorieClient, Qualite, TypeTitre, Client, \
    Titre, Operation, Etablissement, Ville, User, CategorieAction


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

    class Meta:
        model = User
        fields = '__all__'
        exclude = ["password"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-solid'}),
            'username': forms.TextInput(attrs={'class': 'form-control form-control-solid'}),
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



class SignInForm(forms.Form):
    email = forms.EmailField(
        max_length=70,required=True,
        widget=forms.EmailInput(attrs={'class': 'kt-input','placeholder': 'Nom d\'utilisateur'})
    )
    user_password  = forms.CharField(
        max_length=200,required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe','name': 'user_password'
        })
    )

