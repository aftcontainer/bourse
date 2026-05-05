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

class Devise(AbstractModel):
    libelle = models.CharField(max_length=50)
    code_devise = models.IntegerField()
    cours_devise = models.FloatField()

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'DEVISE'


class Pays(AbstractModel):
    indicatif_pays = models.CharField(max_length=8)
    nom_pays = models.CharField(max_length=7,unique=True)
    devise_pays = models.ForeignKey(to='devise',on_delete=models.SET_NULL,null=True,blank=True)

    def __str__(self):
        return self.nom_pays

    class Meta:
        db_table = 'Pays'


class TypePiece(AbstractModel):
    libelle = models.CharField(max_length=50,unique=True)

    class Meta:
        db_table = 'TYPEPIECE'


class TypeOperation(AbstractModel):
    libelle = models.CharField(max_length=50,unique=True)
    mvnt_operation = models.CharField(max_length=50)
    commission = models.FloatField()
    tva = models.FloatField()
    rcm = models.FloatField()
    css = models.FloatField()

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'TYPE_OPERATION'


class CategorieClient(AbstractModel):
    libelle = models.CharField(max_length=100)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'CATEGORIE_CLIENT'


class Qualite(AbstractModel):
    libelle = models.CharField(max_length=50)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'QUALITE'


class TypeTitre(AbstractModel):
    libelle = models.CharField(max_length=50)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'TYPE_TITRE'

class Client(AbstractModel):
    category_client = models.ForeignKey(CategorieClient,on_delete=models.CASCADE)
    nom_client = models.CharField(max_length=100)
    prenom_client = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)
    bp_client = models.CharField(max_length=10,null=True,blank=True)
    tel_client = models.CharField(max_length=15,null=True,blank=True)
    fax_client = models.CharField(max_length=20,null=True,blank=True)
    tx_commission = models.FloatField(default=0.0)
    exonerer_taxe = models.BooleanField(default=False)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=200)
    num_carte = models.CharField(max_length=30)
    matricule = models.CharField(max_length=20)
    qualite = models.ForeignKey(Qualite,on_delete=models.DO_NOTHING)
    pays = models.ForeignKey(Pays,on_delete=models.DO_NOTHING)
    email_client = models.EmailField(max_length=50)
    type_piece = models.ForeignKey(TypePiece,on_delete=models.DO_NOTHING)
    site_client = models.CharField(max_length=100,null=True,blank=True)
    ca_code = models.BooleanField(default=True)
    indentifiant = models.IntegerField()

    def __str__(self):
        return f'{self.nom_client} {self.prenom_client}'

    class Meta:
        db_table = 'CLIENT'


class Titre(AbstractModel):
    type_titre = models.ForeignKey(TypeTitre,on_delete=models.CASCADE)
    libelle = models.CharField(max_length=100)
    nominal = models.IntegerField()
    devise = models.ForeignKey(Devise,on_delete=models.DO_NOTHING)
    quotite = models.IntegerField()
    nb_mini = models.IntegerField()
    cours = models.IntegerField()
    cours_oblig = models.IntegerField()
    tx_oblig = models.IntegerField()
    logo = models.ImageField()
    dercoupon = models.DateField()
    min_ann = models.IntegerField()
    max_ann = models.IntegerField()
    nb_actions = models.IntegerField()
    date_inf = models.DateField()

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'Titre'


class Operation(AbstractModel):
    num_ordre = models.IntegerField()
    num_seq_ordre = models.IntegerField()
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    nb_titre = models.IntegerField()
    cours_operation = models.IntegerField()
    date_ordre = models.DateField()
    montant = models.PositiveIntegerField()

    class Meta:
        db_table = 'OPERATION'


class Etablissement(AbstractModel):
    libelle = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)
    bp_etablissement = models.CharField(max_length=10,null=True,blank=True)
    tx_commission = models.PositiveIntegerField()
    tx_tax = models.PositiveIntegerField()
    logo = models.ImageField(null=True,blank=True)
    plafond_commission = models.PositiveIntegerField()
    tx_commission2 = models.FloatField()
    tx_commission3 = models.FloatField()
    min_commission = models.FloatField()
    tx_retro = models.FloatField()
    mt_retro = models.FloatField()
    signe_etablissement = models.CharField(max_length=20,null=True,blank=True)
    min_retro = models.PositiveIntegerField()
    orgaprinc = models.BooleanField(default=False)
    orga_fin = models.BooleanField(default=False)

    def __str__(self):
        return self.libelle

    class Meta:
        db_table = 'ETABLISSEMENT'


class Compte(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    etablissement = models.ForeignKey(Etablissement,on_delete=models.CASCADE)

    class Meta:
        db_table = 'COMPTE'


class PORTEFEUIL(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    titre = models.ForeignKey(Titre,on_delete=models.CASCADE)
    nb_titre = models.PositiveIntegerField()

    class Meta:
        db_table = 'PORTEFEUIL'


class Histo(AbstractModel):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    operation = models.ForeignKey(Operation,on_delete=models.CASCADE)

    class Meta:
        db_table = 'HISTORIQUE'