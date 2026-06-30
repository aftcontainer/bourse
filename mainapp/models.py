import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import Http404

from mainapp.abstract.models import AbstractModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_object_by_public_id(self, public_id):
        try:
            instance = self.get(public_id=public_id)
            return instance
        except (ObjectDoesNotExist, ValueError, TypeError):
            return Http404

    def create_user(self, email, username, password=None, **kwargs):
        if email is None:
            raise TypeError("Veuillez renseignez l'adresse email de l'utilisateur")
        if password is None:
            raise TypeError("Veuillez saisir unmot de passe")
        if username is None:
            username = email.split('@')[0]
        user = self.model(username=username, email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username=None, password=None, **kwargs):
        if email is None:
            raise TypeError("Veuillez renseignez l'adresse email de l'utilisateur")
        if password is None:
            raise TypeError("Veuillez saisir unmot de passe")
        if username is None:
            username = email.split('@')[0]
        user = self.create_user(username, email, password, **kwargs)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    public_id = models.UUIDField(db_index=True, unique=True, default=uuid.uuid4, editable=False)
    username = models.CharField(db_index=True, max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField('adresse email', unique=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True,
    )

    def __str__(self):
        return self.email

    @property
    def name(self):
        return f"{self.last_name} {self.first_name}"

class Ville(AbstractModel):
    nom_ville = models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.nom_ville

    class Meta:
        db_table = 'VILLE'

class Devise(AbstractModel):
    libelle = models.CharField(max_length=50,unique=True)
    code_devise = models.CharField(max_length=20,unique=True)
    #cours_devise = models.FloatField()
    old_id = models.CharField(max_length=30,null=True,blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'DEVISE'


class Pays(AbstractModel):
    indicatif_pays = models.CharField(max_length=8)
    nom_pays = models.CharField(max_length=7,unique=True)
    devise_pays = models.ForeignKey(to='devise',on_delete=models.SET_NULL,null=True,blank=True)
    old_id = models.IntegerField(null=True,blank=True)

    def __str__(self):
        return self.nom_pays

    class Meta:
        db_table = 'Pays'


class TypePiece(AbstractModel):
    libelle = models.CharField(max_length=50,unique=True)
    old_id = models.IntegerField(null=True,blank=True)

    class Meta:
        db_table = 'TYPEPIECE'


class TypeOperation(AbstractModel):
    libelle = models.CharField(max_length=50)
    mvnt_operation = models.CharField(max_length=50)
    commission = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    tva = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    rcm = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    css = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    old_id = models.CharField(max_length=5,null=True, blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'TYPE_OPERATION'



class CategorieClient(AbstractModel):
    libelle = models.CharField(max_length=100,null=True,blank=True)
    old_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'CATEGORIE_CLIENT'


class Qualite(AbstractModel):
    libelle = models.CharField(max_length=50,unique=True)
    old_id = models.CharField(max_length=15,null=True, blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'QUALITE'


class TypeTitre(AbstractModel):
    libelle = models.CharField(max_length=50)
    old_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'TYPE_TITRE'

class Client(AbstractModel):
    category_client = models.ForeignKey(CategorieClient,on_delete=models.CASCADE)
    nom_client = models.CharField(max_length=100)
    prenom_client = models.CharField(max_length=100,null=True,blank=True)
    adresse = models.CharField(max_length=200,null=True,blank=True)
    nationalite = models.CharField(max_length=50,null=True,blank=True)
    bp_client = models.CharField(max_length=10,null=True,blank=True)
    ville = models.CharField(max_length=50,null=True,blank=True)
    tel_client = models.CharField(max_length=15,null=True,blank=True)
    fax_client = models.CharField(max_length=20,null=True,blank=True)
    tx_commission = models.FloatField(default=0.0,null=True,blank=True)
    exonerer_taxe = models.CharField(max_length=10,null=True,blank=True)
    date_naissance = models.DateField(null=True,blank=True)
    lieu_naissance = models.CharField(max_length=200,null=True,blank=True)
    banque = models.ForeignKey(to='etablissement',null=True,blank=True,on_delete=models.SET_NULL)
    num_carte = models.CharField(max_length=30,null=True,blank=True)
    matricule = models.CharField(max_length=20,null=True,blank=True)
    num_compte = models.CharField(max_length=50,null=True,blank=True)
    qualite = models.ForeignKey(Qualite,on_delete=models.SET_NULL,null=True,blank=True)
    pays = models.ForeignKey(Pays,on_delete=models.SET_NULL,null=True,blank=True)
    email_client = models.EmailField(max_length=50)
    type_piece = models.ForeignKey(TypePiece,null=True,blank=True,on_delete=models.SET_NULL)
    site_client = models.CharField(max_length=100,null=True,blank=True)
    nature_carte = models.CharField(max_length=30,null=True,blank=True)
    ca_code = models.CharField(max_length=13,null=True,blank=True)
    indentifiant = models.IntegerField(null=True,blank=True)
    old_id = models.IntegerField(null=True, blank=True)
    date_creat = models.DateField(null=True,blank=True)
    nom_creat = models.CharField(max_length=50,null=True,blank=True)
    nom_modif = models.CharField(max_length=50,null=True,blank=True)
    date_modif = models.DateField(null=True,blank=True)

    def __str__(self):
        return f'{self.nom_client} {self.prenom_client}'

    class Meta:
        db_table = 'CLIENT'


class Titre(AbstractModel):
    type_titre = models.ForeignKey(TypeTitre,on_delete=models.CASCADE)
    libelle = models.CharField(max_length=100)
    nominal = models.IntegerField()
    devise = models.ForeignKey(Devise,on_delete=models.DO_NOTHING)
    quotite = models.IntegerField(null=True,blank=True)
    nb_mini = models.IntegerField(null=True,blank=True)
    cours = models.IntegerField(null=True,blank=True)
    cours_oblig = models.IntegerField(null=True,blank=True)
    tx_oblig = models.DecimalField(max_digits=5,decimal_places=3,null=True,blank=True)
    datech = models.DateField(null=True,blank=True)
    nom_creat = models.CharField(max_length=50,null=True,blank=True)
    date_creat = models.DateField(null=True,blank=True)
    nom_modif = models.CharField(max_length=50, null=True, blank=True)
    date_modif = models.DateField(null=True, blank=True)
    logo = models.ImageField(null=True,blank=True)
    dercoupon = models.DateField(null=True,blank=True)
    min_ann = models.IntegerField(null=True,blank=True)
    max_ann = models.IntegerField(null=True,blank=True)
    nb_actions = models.IntegerField(null=True,blank=True)
    date_inf = models.DateField(null=True,blank=True)
    rcm = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    tx_visa = models.IntegerField(null=True,blank=True)
    css = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    old_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'Titre'

#A revoir - Cette classe peut etre etre remplacé par
class Operation(AbstractModel):
    num_ordre = models.IntegerField()
    num_seq_ordre = models.IntegerField()
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    nb_titre = models.IntegerField()
    cours_operation = models.IntegerField()
    date_ordre = models.DateField()
    montant = models.PositiveIntegerField()
    old_id = models.IntegerField(null=True, blank=True)
    #sens_op = models.CharField(max_length=10)

    class Meta:
        db_table = 'OPERATION'


class Etablissement(AbstractModel):
    libelle = models.CharField(max_length=100,unique=True)
    adresse = models.CharField(max_length=200,null=True,blank=True)
    bp_etablissement = models.CharField(max_length=10,null=True,blank=True)
    logo = models.ImageField(null=True,blank=True)
    tx_commission = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    tx_tax = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    plafond_commission = models.PositiveIntegerField(null=True,blank=True)
    plafond_commission2 = models.PositiveIntegerField(null=True,blank=True)
    plafond_commission3 = models.PositiveIntegerField(null=True,blank=True)
    tx_commission2 = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    tx_commission3 = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    min_commission = models.PositiveIntegerField(null=True,blank=True)
    tx_retro = models.DecimalField(max_digits=7,decimal_places=5,null=True,blank=True)
    mt_retro = models.IntegerField(null=True,blank=True)
    sigle = models.CharField(max_length=10,null=True,blank=True)
    min_retro = models.PositiveIntegerField(null=True,blank=True)
    orgaprinc = models.CharField(max_length=2,null=True,blank=True)
    orga_fin = models.CharField(max_length=2,null=True,blank=True)
    type_com = models.CharField(max_length=2,null=True,blank=True)
    old_id = models.IntegerField(null=True, blank=True)
    nom_creat = models.CharField(max_length=100,null=True,blank=True)
    date_creat = models.DateField(null=True,blank=True)
    nom_modif = models.CharField(max_length=100,null=True,blank=True)
    date_modif = models.DateField(null=True,blank=True)
    ville = models.ForeignKey(to='ville',on_delete=models.CASCADE,default=1)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'ETABLISSEMENT'


class Compte(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    #etablissement = models.ForeignKey(Etablissement,on_delete=models.CASCADE)
    old_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'COMPTE'


class Portefeuille(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    titre = models.ForeignKey(Titre,on_delete=models.CASCADE)
    etablissement = models.ForeignKey(Etablissement,on_delete=models.CASCADE)
    nb_titre = models.PositiveIntegerField()
    dernier_mouv = models.DateField(null=True,blank=True)
    nom_creat = models.CharField(max_length=100, null=True, blank=True)
    date_creat = models.DateField(null=True, blank=True)
    nom_modif = models.CharField(max_length=100, null=True, blank=True)
    date_modif = models.DateField(null=True, blank=True)
    old_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'PORTEFEUILLE'


class Histo(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    operation = models.ForeignKey(Operation,on_delete=models.CASCADE)
    old_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'HISTORIQUE'

class Nantis(AbstractModel):
    #etablissement = models.ForeignKey(to='etablissement',on_delete=models.DO_NOTHING)
    nb_titre_nanti = models.IntegerField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.CharField(max_length=200,null=True,blank=True)
    old_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'NANTI'


class IndexTitre(AbstractModel):
    client = models.ForeignKey(to='client', on_delete=models.CASCADE, null=True, blank=True)
    etablissement = models.ForeignKey(to='etablissement', on_delete=models.CASCADE,null=True,blank=True)
    titre = models.ForeignKey(to='Titre', on_delete=models.CASCADE,null=True,blank=True)
    nb_titre = models.IntegerField(null=True,blank=True)
    debut_index = models.IntegerField()
    fin_index = models.IntegerField()
    statut_tire = models.IntegerField(default=1)
    nom_creat = models.CharField(max_length=100, null=True, blank=True)
    date_creat = models.DateField(null=True, blank=True)
    nom_modif = models.CharField(max_length=100, null=True, blank=True)
    date_modif = models.DateField(null=True, blank=True)
    indordre = models.IntegerField(null=True, blank=True)
    old_id = models.IntegerField(null=True,blank=True)

    class Meta:
        db_table = 'INDEXTITRE'


class Entreprise(AbstractModel):
    libelle = models.CharField(max_length=100,unique=True)
    logo = models.ImageField(null=True,blank=True)

    class Meta:
        db_table = 'ENTREPRISE'

class CategorieAction(AbstractModel):
    code_cat = models.CharField(max_length=5)
    libelle_cat = models.CharField(max_length=20,unique=True)

    class Meta:
        db_table = 'CATEGORIE_ACTION'
