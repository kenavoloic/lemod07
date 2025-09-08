# gestion_groupes/managers.py
# gato
from django.db import models
from django.contrib.auth.models import User, Group
from gestion_groupes.config import get_groupes_evaluateurs

class ProfilUtilisateurManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user',
            'service'
        ).prefetch_related(
            'user__groups',
            'user__groups__permissions'
        )

    def avec_groupes(self):
        """Profils avec leurs groupes étendus et permissions chargés."""
        return self.get_queryset().prefetch_related(
            'user__groups__groupe_etendu',
        )

    def evaluateurs_actifs(self):
        """Profils actifs appartenant à un groupe autorisé à évaluer."""
        groupes_autorises = get_groupes_evaluateurs()
        return self.filter(
            actif=True,
            user__groups__name__in=groupes_autorises
        ).distinct()

class GroupeEtenduManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('group')

    def avec_statistiques(self):
        """Ajoute des annotations pour le nombre d'utilisateurs et permissions."""
        return self.get_queryset().annotate(
            nb_utilisateurs=models.Count('group__user', distinct=True),
            nb_permissions=models.Count('group__permissions', distinct=True)
        )

    def avec_utilisateurs_et_permissions(self):
        """Charge les utilisateurs, leurs profils et les permissions du groupe."""
        return self.get_queryset().prefetch_related(
            'group__user_set__profil',
            'group__permissions'
        )
