# gestion_groupes/signals.py
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group, User


@receiver(post_save, sender='auth.User')
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement un profil utilisateur lors de la création d'un user"""
    from .models import ProfilUtilisateur
    
    if created:
        from suivi_conducteurs.models import Service
        service_none, _ = Service.objects.get_or_create(
            nom='Non défini',
            defaults={'abreviation': 'ND'}
        )
        ProfilUtilisateur.objects.get_or_create(
            user=instance,
            defaults={
                'actif': instance.is_active,
                'service': service_none,
                'poste': 'Non défini',
            }
        )
    else:
        # Mettre à jour le profil si il existe
        try:
            profil = instance.profil
            profil.actif = instance.is_active
            profil.save()
        except ProfilUtilisateur.DoesNotExist:
            # Créer le profil s'il n'existe pas
            from suivi_conducteurs.models import Service
            service_none, _ = Service.objects.get_or_create(
                nom='Non défini',
                defaults={'abreviation': 'ND'}
            )
            ProfilUtilisateur.objects.create(
                user=instance,
                actif=instance.is_active,
                service=service_none,
                poste='Non défini',
            )


@receiver(post_save, sender='auth.Group')
def create_or_update_group_extended(sender, instance, created, **kwargs):
    """Créer automatiquement une extension de groupe"""
    from .models import GroupeEtendu
    
    if created:
        GroupeEtendu.objects.get_or_create(
            group=instance,
            defaults={
                'description': f'Groupe {instance.name}',
                'couleur': '#007bff',
                'niveau_acces': 1,
                'actif': True,
            }
        )


@receiver(m2m_changed, sender=Group.user_set.through)
def track_user_group_changes(sender, instance, action, pk_set, **kwargs):
    """Suivre les changements d'affectation des utilisateurs aux groupes"""
    from .models import HistoriqueGroupes
    
    if action == "post_add":
        for user_pk in pk_set:
            try:
                user = User.objects.get(pk=user_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='add_user',
                    utilisateur_cible=user,
                    details=f'Ajout de {user.username} au groupe {instance.name}'
                )
                
                # NOUVEAU : Créer automatiquement un évaluateur si ajouté à RH ou Exploitation
                create_evaluateur_if_needed(user)
                
            except User.DoesNotExist:
                pass
    
    elif action == "post_remove":
        for user_pk in pk_set:
            try:
                user = User.objects.get(pk=user_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='remove_user',
                    utilisateur_cible=user,
                    details=f'Retrait de {user.username} du groupe {instance.name}'
                )
                
                # NOUVEAU : Vérifier s'il faut supprimer l'évaluateur
                update_evaluateur_status(user)
                
            except User.DoesNotExist:
                pass


def create_evaluateur_if_needed(user):
    """
    Crée automatiquement un évaluateur si l'utilisateur appartient à RH ou Exploitation
    et possède les informations requises
    """
    from suivi_conducteurs.models import Evaluateur, Service
    
    # Vérifier si l'utilisateur appartient à RH ou Exploitation
    groupes_evaluateurs = ['RH', 'Exploitation']
    user_groups = user.groups.filter(name__in=groupes_evaluateurs).values_list('name', flat=True)
    
    if user_groups:
        # L'utilisateur est dans un groupe évaluateur
        try:
            evaluateur = Evaluateur.objects.get(user=user)
            # Mettre à jour le service si nécessaire
            nouveau_service = determine_service_from_groups(list(user_groups))
            if nouveau_service and evaluateur.service != nouveau_service:
                evaluateur.service = nouveau_service
                evaluateur.save()
                print(f"Service de l'évaluateur {user.username} mis à jour : {nouveau_service.nom}")
        
        except Evaluateur.DoesNotExist:
            # Créer un nouvel évaluateur seulement si les données sont suffisantes
            service = determine_service_from_groups(list(user_groups))
            if service and can_create_evaluateur(user):
                # Utiliser les données du profil utilisateur si disponibles
                nom, prenom = get_user_full_name(user)
                
                evaluateur = Evaluateur.objects.create(
                    user=user,
                    nom=nom,
                    prenom=prenom,
                    service=service
                )
                print(f"✅ Évaluateur créé automatiquement pour {user.username} dans le service {service.nom}")
            else:
                print(f"⚠️ Impossible de créer l'évaluateur pour {user.username} : données insuffisantes ou service manquant")


def update_evaluateur_status(user):
    """
    Met à jour le statut de l'évaluateur quand l'utilisateur change de groupes
    """
    from suivi_conducteurs.models import Evaluateur
    
    # Vérifier si l'utilisateur a encore des groupes évaluateurs
    groupes_evaluateurs = ['RH', 'Exploitation']
    user_groups = user.groups.filter(name__in=groupes_evaluateurs).values_list('name', flat=True)
    
    try:
        evaluateur = Evaluateur.objects.get(user=user)
        
        if not user_groups:
            # Plus aucun groupe évaluateur - vous pouvez choisir de :
            # Option 1 : Supprimer l'évaluateur
            # evaluateur.delete()
            # print(f"Évaluateur supprimé pour {user.username} (plus dans RH/Exploitation)")
            
            # Option 2 : Désactiver (si vous ajoutez un champ 'actif' au modèle Evaluateur)
            # evaluateur.actif = False
            # evaluateur.save()
            
            # Option 3 : Ne rien faire (garder l'évaluateur)
            print(f"Utilisateur {user.username} retiré des groupes évaluateurs mais évaluateur conservé")
        else:
            # Mettre à jour le service selon les nouveaux groupes
            nouveau_service = determine_service_from_groups(list(user_groups))
            if nouveau_service and evaluateur.service != nouveau_service:
                evaluateur.service = nouveau_service
                evaluateur.save()
                print(f"Service de l'évaluateur {user.username} mis à jour : {nouveau_service.nom}")
    
    except Evaluateur.DoesNotExist:
        # Pas d'évaluateur existant, en créer un si nécessaire
        if user_groups:
            create_evaluateur_if_needed(user)


# def determine_service_from_groups(group_names):
#     """
#     Détermine le service selon les groupes de l'utilisateur
#     Priorité : RH > Exploitation
#     """
#     from suivi_conducteurs.models import Service
    
#     try:
#         if 'RH' in group_names:
#             return Service.objects.get(nom='Ressources Humaines')
#         elif 'Exploitation' in group_names:
#             return Service.objects.get(nom='Exploitation')
#     except Service.DoesNotExist:
#         print(f"Service non trouvé pour les groupes : {group_names}")
#         return None
    
#     return None

# Remplacez cette fonction dans votre signals.py

def determine_service_from_groups(group_names):
    """
    Détermine le service selon les groupes de l'utilisateur
    Priorité : RH > Exploitation
    """
    from suivi_conducteurs.models import Service
    
    try:
        if 'RH' in group_names:
            # Créer le service s'il n'existe pas
            service, created = Service.objects.get_or_create(
                nom='Ressources Humaines',
                defaults={'abreviation': 'RH'}
            )
            if created:
                print(f"✅ Service 'Ressources Humaines' créé automatiquement")
            return service
            
        elif 'Exploitation' in group_names:
            # Créer le service s'il n'existe pas
            service, created = Service.objects.get_or_create(
                nom='Exploitation',
                defaults={'abreviation': 'EXP'}
            )
            if created:
                print(f"✅ Service 'Exploitation' créé automatiquement")
            return service
            
    except Exception as e:
        print(f"❌ Erreur lors de la création/récupération du service : {e}")
        return None
    
    return None


def can_create_evaluateur(user):
    """
    Vérifie si un évaluateur peut être créé pour cet utilisateur
    Critères : nom et prénom disponibles, utilisateur actif
    """
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        return False
    
    # Vérifier qu'on a au moins un nom ou prénom significatif
    nom, prenom = get_user_full_name(user)
    
    # Au moins un des deux doit être différent de la valeur par défaut
    if nom == 'Nom' and prenom == 'Prénom':
        return False
    
    return True


def get_user_full_name(user):
    """
    Récupère le nom et prénom de l'utilisateur en utilisant plusieurs sources
    Priorité : User.first_name/last_name > ProfilUtilisateur > valeurs par défaut
    """
    nom = user.last_name.strip() if user.last_name else ''
    prenom = user.first_name.strip() if user.first_name else ''
    
    # Si les données Django User sont vides, essayer le profil utilisateur
    if not nom and not prenom:
        try:
            profil = user.profil
            # Le modèle ProfilUtilisateur n'a pas de champs nom/prénom directs
            # mais on peut extraire du full_name si disponible
            pass
        except:
            pass
    
    # Valeurs par défaut si rien trouvé
    nom = nom or 'Nom'
    prenom = prenom or 'Prénom'
    
    return nom, prenom


@receiver(m2m_changed, sender=Group.permissions.through)
def track_group_permission_changes(sender, instance, action, pk_set, **kwargs):
    """Suivre les changements de permissions des groupes"""
    from django.contrib.auth.models import Permission
    from .models import HistoriqueGroupes
    
    if action == "post_add":
        for perm_pk in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='add_permission',
                    permission_cible=permission,
                    details=f'Ajout de la permission {permission.name} au groupe {instance.name}'
                )
            except Permission.DoesNotExist:
                pass
    
    elif action == "post_remove":
        for perm_pk in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='remove_permission',
                    permission_cible=permission,
                    details=f'Retrait de la permission {permission.name} du groupe {instance.name}'
                )
            except Permission.DoesNotExist:
                pass


@receiver(post_delete, sender='auth.Group')
def track_group_deletion(sender, instance, **kwargs):
    """Suivre la suppression des groupes"""
    # Note: On ne peut pas créer d'HistoriqueGroupes car la FK vers Group sera cassée
    # Alternative : logger l'événement
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Suppression du groupe {instance.name} (ID: {instance.id})')
