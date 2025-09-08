#gestion_groupes/models.py
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from gestion_groupes.config import get_groupes_evaluateurs

class ProfilUtilisateur(models.Model):
    """Extension du modèle User avec des informations supplémentaires"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil', verbose_name="Utilisateur")
    nom = models.CharField(max_length=255, blank=True, verbose_name="Nom", help_text="Nom de famille")
    prenom = models.CharField(max_length=255, blank=True, verbose_name="Prénom", help_text="Prénom")
    telephone = models.CharField(max_length=15, blank=True, verbose_name="Téléphone")
    service = models.ForeignKey(
        'suivi_conducteurs.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Service"
    )
    poste = models.CharField(max_length=100, blank=True, verbose_name="Poste")
    date_embauche = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    actif = models.BooleanField(default=True, verbose_name="Compte actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

    def peut_evaluer(self):
        groupes_autorises = set(get_groupes_evaluateurs()) 
        return any(groupe.name in groupes_autorises for groupe in self.user.groups.all())
    
    @property
    def nom_complet(self):
        """retourne le nom complet en utilisant les données de ProfilUtilisateur"""
        nom = self.nom if self.nom else self.user.last_name
        prenom = self.prenom if self.prenom else self.user.first_name
        return f"{nom} {prenom}"
    
    @property
    def groupes_utilisateur(self):
        return self.user.groups.all()
    
    def clean(self):
        if self.telephone and not self.telephone.replace(' ', '').replace('-', '').replace('.', '').isdigit():
            raise ValidationError({'telephone': 'Le numéro de téléphone ne doit contenir que des chiffres, espaces, tirets ou points.'})
        if not self.nom and not self.user.last_name:
            raise ValidationError({'nom': "Un nom de famille est requis."})
        if not self.prenom and not self.user.first_name:
            raise ValidationError({'prenom': "Un prénom est requis."})

    def save(self, *args, **kwargs):
        """ Sauvegarde le profil et remplit automatiquement les nom et prenom si ceux-ci sont vides"""
        if not self.nom and self.user.last_name:
            self.nom = self.user.last_name
        if not self.prenom and self.user.first_name:
            self.prenom = self.user.first_name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
        ordering = ['user__last_name', 'user__first_name']
    

class GroupeEtendu(models.Model):
    """Extension du modèle Group avec des informations supplémentaires"""
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='groupe_etendu')
    description = models.TextField(blank=True, verbose_name="Description du groupe")
    couleur = models.CharField(
        max_length=7, 
        default='#007bff',
        verbose_name="Couleur d'affichage",
        help_text="Code couleur hexadécimal (ex: #007bff)"
    )
    niveau_acces = models.IntegerField(
        default=1,
        verbose_name="Niveau d'accès",
        help_text="Plus le nombre est élevé, plus les privilèges sont importants"
    )
    actif = models.BooleanField(default=True, verbose_name="Groupe actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Groupe étendu"
        verbose_name_plural = "Groupes étendus"
        ordering = ['-niveau_acces', 'group__name']
    
    def __str__(self):
        return f"{self.group.name} (Niveau {self.niveau_acces})"
    
    @property
    def nombre_utilisateurs(self):
        return self.group.user_set.count()
    
    @property
    def nombre_permissions(self):
        return self.group.permissions.count()
    
    def clean(self):
        if self.couleur and not self.couleur.startswith('#'):
            self.couleur = f"#{self.couleur}"
        
        if self.couleur and len(self.couleur) != 7:
            raise ValidationError({'couleur': 'La couleur doit être au format hexadécimal (#RRGGBB).'})


class HistoriqueGroupes(models.Model):
    """Historique des modifications de groupes"""
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('add_user', 'Ajout utilisateur'),
        ('remove_user', 'Retrait utilisateur'),
        ('add_permission', 'Ajout permission'),
        ('remove_permission', 'Retrait permission'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='historique')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    utilisateur_modifieur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Utilisateur ayant effectué la modification"
    )
    utilisateur_cible = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='historique_groupes_cible',
        verbose_name="Utilisateur concerné par l'action"
    )
    permission_cible = models.ForeignKey(
        Permission, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Permission concernée par l'action"
    )
    details = models.TextField(blank=True, verbose_name="Détails de l'action")
    date_action = models.DateTimeField(default=timezone.now, verbose_name="Date de l'action")
    
    class Meta:
        verbose_name = "Historique des groupes"
        verbose_name_plural = "Historiques des groupes"
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.group.name} - {self.get_action_display()} - {self.date_action.strftime('%d/%m/%Y %H:%M')}"
