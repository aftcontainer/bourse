from django import forms

from mainapp.models import Devise, Pays, TypePiece, TypeOperation, CategorieClient, Qualite, TypeTitre, Client, \
Titre, Operation, Etablissement


class DeviseForm(forms.ModelForm):

    class Meta:
        model = Devise
        fields = '__all__'


class PaysForm(forms.ModelForm):

    class Meta:
        model = Pays
        fields = '__all__'


class TypePieceForm(forms.ModelForm):

    class Meta:
        model = TypePiece
        fields = '__all__'

class TypeOperationForm(forms.ModelForm):

    class Meta:
        model = TypeOperation
        fields = '__all__'

class CategorieClientForm(forms.ModelForm):

    class Meta:
        model = CategorieClient
        fields = '__all__'


class QualiteForm(forms.ModelForm):

    class Meta:
        model = Qualite
        fields = '__all_'


class TypeTitreForm(forms.ModelForm):

    class Meta:
        model = TypeTitre
        fields = '__all__'


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = '__all__'

class TitreForm(forms.ModelForm):

    class Meta:
        model = Titre
        fields = '__all__'

class OperationForm(forms.ModelForm):

    class Meta:
        model = Operation
        fields = '__all__'

class EtablissementForm(forms.ModelForm):

    class Meta:
        model = Etablissement
        fields = '__all__'


