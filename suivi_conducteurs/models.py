# suivi_conducteurs/models.py
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from gestion_groupes.config import get_groupes_evaluateurs

# ==============================================
# MANAGERS DÉFINIS DANS LE MÊME FICHIER
# ==============================================

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
        return self.get_queryset().prefetch_related(
            models.Prefetch(
                'evaluation_set',
                # Pas besoin d'import, Evaluation est défini après
                queryset=None,  # Sera résolu à l'exécution
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
        return self.get_queryset().prefetch_related(
            models.Prefetch(
                'notes',
                # Note sera défini après, pas de problème
                queryset=None,  # Sera résolu à l'exécution
                to_attr='notes_completes'
            )
        )
    
    def par_periode(self, date_debut, date_fin):
        return self.filter(
            date_evaluation__range=[date_debut, date_fin]
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

# ==============================================
# MODÈLES
# ==============================================

class Site(models.Model):
    """Site auquel est rattaché un conducteur"""
    nom_commune = models.CharField(max_length=255, verbose_name="Commune")
    code_postal = models.CharField(
            max_length = 5,
            verbose_name = "Code postal",
            validators = [
                RegexValidator(regex=r'^\d{5}$', message = "Un code postal est long de 5 caractères")
                ]
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.nom_commune:
            self.nom_commune = self.nom_commune.strip()
        if self.code_postal:
            self.code_postal = self.code_postal.strip()
            if not self.code_postal.isdigit():
                raise ValidationError({'code_postal': 'Le code postal ne doit contenir que des chiffres'})
            if len(self.code_postal) != 5:
                raise ValidationError({'code_postal': 'Le code postal doit contenir exactement 5 chiffres'})

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['nom_commune']

    def __str__(self):
        return f"{self.nom_commune}"

class Societe(models.Model):
    """Société à laquelle un conducteur est rattaché"""
    socid = models.PositiveIntegerField(unique=True)
    socnom = models.CharField(max_length=255, verbose_name="Nom société")
    socactif = models.BooleanField(default=True, verbose_name="Active")
    soccode = models.CharField(max_length=255, verbose_name="Code société")
    soccp = models.CharField(
            max_length = 5,
            verbose_name = "Code postal",
            validators = [
                RegexValidator(regex=r'^\d{5}$', message = "Un code postal est long de 5 caractères")
                ]
    )
    socvillib1 = models.CharField(max_length=255, verbose_name="Ville")
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.socnom:
            self.socnom = self.socnom.strip()
        if self.soccode:
            self.soccode = self.soccode.strip()
     
    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Sociétés"
        ordering = ['socnom']
        indexes = [models.Index(fields=['socnom']),]

    def __str__(self):
        return f"{self.socnom}"

class Service(models.Model):
    """Service auquel est rattaché l'évaluateur"""
    nom = models.CharField(max_length=255, verbose_name="Nom du service")
    abreviation = models.CharField(max_length=10, verbose_name="Abréviation")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom}"

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if self.abreviation:
            self.abreviation = self.abreviation.strip()

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['nom']
        
class Conducteur(models.Model):
    """Caractériques d'un conducteur"""
    salnom = models.CharField(max_length=255, verbose_name="nom")
    salnom2 = models.CharField(max_length=255, verbose_name="prénom")
    salsocid = models.ForeignKey(Societe, to_field='socid', on_delete=models.CASCADE, verbose_name="Société")
    salactif = models.BooleanField(default=True, verbose_name="Conducteur actif")
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Site")
    interim_p = models.BooleanField(default=True, verbose_name="Intérim")
    sous_traitant_p = models.BooleanField(default=True, verbose_name="Sous-traitant")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    date_creation = models.DateTimeField(auto_now_add=True)

    # Manager sans import circulaire
    objects = ConducteurManager()

    def clean(self):
        if self.salnom:
            self.salnom = self.salnom.strip()
        if self.salnom2:
            self.salnom2 = self.salnom2.strip()
        
    def __str__(self):
        return f"{self.salnom}"

    @property
    def nom_complet(self):
        return f"{self.salnom} {self.salnom2}"

    def get_last_evaluation_score(self):
        """Retourne le score de la dernière évaluation de ce conducteur"""
        # Si les évaluations sont déjà préchargées
        if hasattr(self, 'evaluations_recentes') and self.evaluations_recentes:
            derniere_evaluation = self.evaluations_recentes[0]
            return derniere_evaluation.calculate_score()
        
        # Sinon, requête optimisée
        derniere_evaluation = self.evaluation_set.select_related(
            'type_evaluation'
        ).prefetch_related(
            'notes__critere'
        ).order_by('-date_evaluation').first()
        
        if derniere_evaluation:
            return derniere_evaluation.calculate_score()
        return None

    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        ordering = ['salnom','salnom2']

class Evaluateur(models.Model):
    """Utilisateur effectuant l'évaluation d'un conducteur"""
    nom = models.CharField(max_length=255, verbose_name="nom")
    prenom = models.CharField(max_length=255, verbose_name="prénom")
    user = models.OneToOneField(
        'auth.User', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Compte utilisateur",
        help_text="Compte utilisateur Django associé à cet évaluateur"
    )

    # Manager sans import circulaire
    objects = EvaluateurManager()

    def __str__(self):
        nom_service = self.service if self.service else "Service non défini"
        return f"{nom_service} : {self.nom} {self.prenom}"

    @property
    def service(self):
        """Au lieu de le gérer depuis ce modèle. Les services sont déterminés au niveau de gestion_groupes/models.py and le profilUtilisateur """
        if hasattr(self, 'user') and self.user and hasattr(self.user, 'profil'):
            return self.user.profil.service
        return None
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def peut_evaluer(self):
        """Version optimisée avec cache"""
        if not hasattr(self, '_peut_evaluer_cache'):
            if hasattr(self, 'user') and self.user and hasattr(self.user, 'profil'):
                self._peut_evaluer_cache = self.user.profil.peut_evaluer()
            else:
                self._peut_evaluer_cache = False
        return self._peut_evaluer_cache
    
    def get_user_groups(self):
        """Retourne les groupes de l'utilisateur associé"""
        if hasattr(self, 'user') and self.user:
            # Si les groupes sont préchargés, on les utilise
            if hasattr(self.user, '_prefetched_objects_cache') and 'groups' in self.user._prefetched_objects_cache:
                return [group.name for group in self.user.groups.all()]
            return list(self.user.groups.values_list('name', flat=True))
        return []
    
    def clean(self):
        if hasattr(self, 'nom') and self.nom:
            self.nom = self.nom.strip()
        if hasattr(self, 'prenom') and self.prenom:
            self.prenom = self.prenom.strip()

        if self.user and not self.peut_evaluer():
            raise ValidationError(
                {'user': f"{self.nom_complet} n'appartient pas à un groupe pouvant faire des évaluations de conducteur."}
            )

    def save(self, *args, **kwargs):
        if hasattr(self, 'user') and self.user and hasattr(self.user, 'profil'):
            if not self.user.profil.nom and self.nom:
                self.user.profil.nom = self.nom
            if not self.user.profil.prenom and self.prenom:
                self.user.profil.prenom = self.prenom
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Évaluateur"
        verbose_name_plural = "Évaluateurs"
        ordering = ['nom', 'prenom']            

class TypologieEvaluation(models.Model):
    """ Types d'évaluation : avant le recrutement, évaluation de la conduite, évaluation du comportement"""
    nom = models.CharField(max_length=255, verbose_name="Nom")
    abreviation = models.CharField(max_length=10, verbose_name="Abréviation")
    description = models.TextField(verbose_name="Description")

    def __str__(self):
        return f"{self.nom}"

    class Meta:
        verbose_name="Type d'évaluation"
        verbose_name_plural = "Types d'évaluation"

class CritereEvaluation(models.Model):
    """Critères d'évaluation d'un conducteur"""
    nom = models.CharField(max_length=255)
    numero_ordre = models.PositiveIntegerField(unique=True, editable=False, blank=True, null=True)
    type_evaluation = models.ForeignKey(TypologieEvaluation, on_delete=models.CASCADE)
    valeur_mini = models.PositiveIntegerField()
    valeur_maxi = models.PositiveIntegerField()
    actif = models.BooleanField(default=True, help_text="Critère actuellement utilisé")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.valeur_mini}-{self.valeur_maxi})"

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                dernier_numero_ordre = CritereEvaluation.objects.select_for_update().aggregate(
                    max_numero_ordre = models.Max('numero_ordre')
                    )['max_numero_ordre']
                self.numero_ordre = (dernier_numero_ordre or 0) + 1
        super().save(*args, **kwargs)

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            raise ValidationError({'nom': "Un nom de critère est requis."})
        if self.valeur_mini is not None and self.valeur_maxi is not None:
            if self.valeur_mini >= self.valeur_maxi:
                raise ValidationError('La valeur minimale doit être inférieure à la valeur maximale.')

    class Meta:
        verbose_name = "Critère d'évaluation"
        verbose_name_plural = "Critères d'évaluation"
        ordering = ['numero_ordre']

class Evaluation(models.Model):
    """Session de notation regroupant toutes les notes d'un conducteur par un évaluateur à une date donnée"""
    date_evaluation = models.DateField(verbose_name="Date d'évaluation")
    evaluateur = models.ForeignKey(Evaluateur, on_delete=models.CASCADE, verbose_name="Évaluateur")
    conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE, verbose_name="Conducteur")
    type_evaluation = models.ForeignKey(TypologieEvaluation, on_delete=models.CASCADE, verbose_name="Type d'évaluation")
    date_creation = models.DateTimeField(auto_now_add=True)

    # Manager sans import circulaire
    objects = EvaluationManager()

    def __str__(self):
        return f"{self.date_evaluation} - {self.conducteur} par {self.evaluateur} ({self.type_evaluation})"

    def clean(self):
        if not self.date_evaluation:
            raise ValidationError({'date_evaluation': "Une date d'évaluation est requise."})
        
        if self.pk:
            notes_incompatibles = self.notes.exclude(critere__type_evaluation=self.type_evaluation)
            if notes_incompatibles.exists():
                raise ValidationError({
                    'type_evaluation': "Impossible de changer le type d'évaluation : des notes existent déjà pour d'autres types."
                })

    def calculate_score(self):
        """Version optimisée du calcul de score"""
        # Utiliser les notes préchargées si disponibles
        if hasattr(self, '_prefetched_objects_cache') and 'notes' in self._prefetched_objects_cache:
            notes = [note for note in self.notes.all() 
                    if note.valeur is not None and note.critere.actif]
        else:
            notes = self.notes.select_related('critere').filter(
                valeur__isnull=False,
                critere__actif=True
            )
        
        if not notes:
            return None
        
        total_notes = sum(note.valeur for note in notes)
        total_max = sum(note.critere.valeur_maxi for note in notes)
        
        if total_max == 0:
            return None
        
        score = (total_notes / total_max) * 100
        return round(score, 1)

    def get_completion_status(self):
        """Version optimisée du statut de completion avec cache"""
        if not hasattr(self, '_completion_status_cache'):
            criteres_actifs = CritereEvaluation.objects.filter(
                type_evaluation=self.type_evaluation,
                actif=True
            ).count()
            
            if hasattr(self, '_prefetched_objects_cache') and 'notes' in self._prefetched_objects_cache:
                notes_completes = len([n for n in self.notes.all() if n.valeur is not None])
            else:
                notes_completes = self.notes.filter(valeur__isnull=False).count()
            
            if criteres_actifs == 0:
                status = "Aucun critère actif"
            elif notes_completes == criteres_actifs:
                status = f"✅ Complet ({notes_completes}/{criteres_actifs})"
            else:
                status = f"⚠️ Incomplet ({notes_completes}/{criteres_actifs})"
            
            self._completion_status_cache = status
        
        return self._completion_status_cache
            
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        unique_together = ['conducteur', 'date_evaluation', 'evaluateur', 'type_evaluation']
        ordering = ['-date_evaluation']
        indexes = [
            models.Index(fields=['date_evaluation']),
            models.Index(fields=['conducteur']),
            models.Index(fields=['type_evaluation']),
        ]
        
class Note(models.Model):
    """Note individuelle pour un critère spécifique dans une session d'évaluation"""
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, help_text="Session d'évaluation", related_name='notes')
    critere = models.ForeignKey(CritereEvaluation, on_delete=models.CASCADE, help_text="Critère évalué")
    valeur = models.PositiveIntegerField(null=True, blank=True, help_text="Note attribuée")
    date_creation = models.DateTimeField(auto_now_add=True)

    # Manager sans import circulaire
    objects = NoteManager()

    def __str__(self):
        return f"{self.evaluation.conducteur} - {self.critere.nom}: {self.valeur or 'Non noté'}"

    def clean(self):
        if self.valeur is not None:
            if self.valeur < self.critere.valeur_mini or self.valeur > self.critere.valeur_maxi:
                raise ValidationError({
                    'valeur': f'La note doit être comprise entre {self.critere.valeur_mini} et {self.critere.valeur_maxi}.'
                })
        
        if self.evaluation_id and self.critere_id:
            if self.critere.type_evaluation != self.evaluation.type_evaluation:
                raise ValidationError({
                    'critere': f'Le critère doit correspondre au type d\'évaluation "{self.evaluation.type_evaluation}".'
                })

    @property
    def date_evaluation(self):
        return self.evaluation.date_evaluation

    @property
    def evaluateur(self):
        return self.evaluation.evaluateur

    @property
    def conducteur(self):
        return self.evaluation.conducteur

    @property
    def type_evaluation(self):
        return self.evaluation.type_evaluation
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ['evaluation', 'critere']
        ordering = ['critere__nom']
        indexes = [
            models.Index(fields=['evaluation', 'critere']),
        ]

# ==============================================
# POST-TRAITEMENT DES MANAGERS 
# ==============================================

# Maintenant que tous les modèles sont définis, on peut finaliser les managers
def _finalize_managers():
    """Finalise les managers avec les bonnes références"""
    
    # Mise à jour du ConducteurManager
    ConducteurManager.avec_derniere_evaluation = lambda self: self.get_queryset().prefetch_related(
        models.Prefetch(
            'evaluation_set',
            queryset=Evaluation.objects.select_related(
                'evaluateur__user__profil',
                'type_evaluation'
            ).order_by('-date_evaluation'),
            to_attr='evaluations_recentes'
        )
    )
    
    # Mise à jour de l'EvaluationManager
    EvaluationManager.avec_notes_completes = lambda self: self.get_queryset().prefetch_related(
        models.Prefetch(
            'notes',
            queryset=Note.objects.select_related('critere').filter(
                valeur__isnull=False,
                critere__actif=True
            ).order_by('critere__numero_ordre'),
            to_attr='notes_completes'
        )
    )

# Appel automatique à la fin du module
_finalize_managers()
