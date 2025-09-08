# suivi_conducteurs/managers.py
from django.db import models

class ConducteurManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'salsocid',
            'site'
        )
    
    def actifs(self):
        return self.filter(salactif=True)
    
    def avec_derniere_evaluation(self):
        """Conducteurs avec leur dernière évaluation"""
        from .models import Evaluation
        
        return self.get_queryset().prefetch_related(
            models.Prefetch(
                'evaluation_set',
                queryset=Evaluation.objects.select_related(
                    'evaluateur__user__profil',
                    'type_evaluation'
                ).order_by('-date_evaluation'),
                to_attr='evaluations_recentes'
            )
        )

class EvaluateurManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user__profil__service'
        ).prefetch_related(
            'user__groups'
        )
    
    def pouvant_evaluer(self):
        """Évaluateurs appartenant aux groupes autorisés"""
        from gestion_groupes.config import get_groupes_evaluateurs
        groupes_autorises = get_groupes_evaluateurs()
        return self.filter(
            user__groups__name__in=groupes_autorises
        ).distinct()

class EvaluationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'conducteur__salsocid',
            'conducteur__site',
            'evaluateur__user__profil',
            'type_evaluation'
        )
    
    def avec_notes_completes(self):
        """Évaluations avec toutes leurs notes chargées"""
        from .models import Note
        
        return self.get_queryset().prefetch_related(
            models.Prefetch(
                'notes',
                queryset=Note.objects.select_related('critere').filter(
                    valeur__isnull=False,
                    critere__actif=True
                ).order_by('critere__numero_ordre')
            )
        )
    
    def par_periode(self, date_debut, date_fin):
        return self.filter(
            date_evaluation__range=[date_debut, date_fin]
        )
    
    def statistiques_par_evaluateur(self):
        """Statistiques groupées par évaluateur"""
        return self.values(
            'evaluateur__nom',
            'evaluateur__prenom',
            'evaluateur__user__profil__service__nom'
        ).annotate(
            nb_evaluations=models.Count('id'),
            score_moyen=models.Avg('notes__valeur'),
            derniere_evaluation=models.Max('date_evaluation')
        )

class NoteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'evaluation__conducteur',
            'evaluation__evaluateur',
            'critere'
        )
    
    def completes(self):
        """Notes avec une valeur attribuée"""
        return self.filter(valeur__isnull=False)
