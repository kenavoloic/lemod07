# gestion_groupes/config.py

permissions_modele = {
    'conducteur': ['add', 'change', 'delete', 'view'],
    'evaluateur': ['add', 'change', 'delete', 'view'],
    'site': ['add', 'change', 'delete', 'view'],
    'societe': ['add', 'change', 'delete', 'view'],
    'service': ['add', 'change', 'delete', 'view'],
    'critereevaluation': ['add', 'change', 'delete', 'view'],
    'evaluation': ['add', 'change', 'delete', 'view'],
    'typologieevaluation': ['add', 'change', 'delete', 'view'],
    'note': ['add', 'change', 'delete', 'view'],
}

configuration_groupes = {
    'RH': {
        'display_name': 'Ressources Humaines',
        'description': 'Ressources Humaines - Gestion complète des données',
        'color': '#007bff',
        'evaluer_p': True,
        'django_permissions': [
            # Conducteur - CRUD complet
            'suivi_conducteurs.add_conducteur',
            'suivi_conducteurs.change_conducteur',
            'suivi_conducteurs.delete_conducteur',
            'suivi_conducteurs.view_conducteur',
            
            # Evaluateur - CRUD complet
            'suivi_conducteurs.add_evaluateur',
            'suivi_conducteurs.change_evaluateur',
            'suivi_conducteurs.delete_evaluateur',
            'suivi_conducteurs.view_evaluateur',
            
            # Site - CRUD complet
            'suivi_conducteurs.add_site',
            'suivi_conducteurs.change_site',
            'suivi_conducteurs.delete_site',
            'suivi_conducteurs.view_site',
            
            # Societe - CRUD complet
            'suivi_conducteurs.add_societe',
            'suivi_conducteurs.change_societe',
            'suivi_conducteurs.delete_societe',
            'suivi_conducteurs.view_societe',
            
            # Service - CRUD complet
            'suivi_conducteurs.add_service',
            'suivi_conducteurs.change_service',
            'suivi_conducteurs.delete_service',
            'suivi_conducteurs.view_service',
            
            # CritereEvaluation - CRUD complet
            'suivi_conducteurs.add_critereevaluation',
            'suivi_conducteurs.change_critereevaluation',
            'suivi_conducteurs.delete_critereevaluation',
            'suivi_conducteurs.view_critereevaluation',
            
            # Evaluation - CRUD complet
            'suivi_conducteurs.add_evaluation',
            'suivi_conducteurs.change_evaluation',
            'suivi_conducteurs.delete_evaluation',
            'suivi_conducteurs.view_evaluation',
            
            # TypologieEvaluation - CRUD complet
            'suivi_conducteurs.add_typologieevaluation',
            'suivi_conducteurs.change_typologieevaluation',
            'suivi_conducteurs.delete_typologieevaluation',
            'suivi_conducteurs.view_typologieevaluation',
            
            # Note - CRUD complet
            'suivi_conducteurs.add_note',
            'suivi_conducteurs.change_note',
            'suivi_conducteurs.delete_note',
            'suivi_conducteurs.view_note',
        ],

    },
    
    'Exploitation': {
        'display_name': 'Exploitation',
        'description': 'Exploitation - Évaluations et consultation des conducteurs',
        'color': '#28a745',
        'evaluer_p': True,
        'django_permissions': [
            # Conducteur - Consultation et modification seulement
            'suivi_conducteurs.view_conducteur',
            'suivi_conducteurs.change_conducteur',
            
            # Evaluation - CRUD complet
            'suivi_conducteurs.add_evaluation',
            'suivi_conducteurs.change_evaluation',
            'suivi_conducteurs.delete_evaluation',
            'suivi_conducteurs.view_evaluation',
            
            # Note - CRUD complet
            'suivi_conducteurs.add_note',
            'suivi_conducteurs.change_note',
            'suivi_conducteurs.delete_note',
            'suivi_conducteurs.view_note',
            
            # Permissions de lecture pour les données liées
            'suivi_conducteurs.view_evaluateur',
            'suivi_conducteurs.view_site',
            'suivi_conducteurs.view_societe',
            'suivi_conducteurs.view_service',
            'suivi_conducteurs.view_critereevaluation',
            'suivi_conducteurs.view_typologieevaluation',
        ],

    },
    
    'Direction': {
        'display_name': 'Direction',
        'description': 'Direction - Consultation et rapports',
        'color': '#6f42c1',
        'level': 4,
        'evaluer_p': False,
        'django_permissions': [         
            'suivi_conducteurs.view_conducteur',
            'suivi_conducteurs.view_evaluateur',
            'suivi_conducteurs.view_site',
            'suivi_conducteurs.view_societe',
            'suivi_conducteurs.view_service',
            'suivi_conducteurs.view_critereevaluation',
            'suivi_conducteurs.view_evaluation',
            'suivi_conducteurs.view_typologieevaluation',
            'suivi_conducteurs.view_note',
        ],

    },
    

}

# ==============================================

def get_group_permissions(group_key):
    """Retourne toutes les permissions d'un groupe"""
    if group_key not in configuration_groupes:
        return []
    
    group_config = configuration_groupes[group_key]
    django_perms = group_config.get('django_permissions', [])
    
    return {
        'django_permissions': django_perms,
    }

def get_group_level(group_key):
    """Retourne le niveau d'un groupe"""
    return configuration_groupes.get(group_key, {}).get('level', 1)

def get_group_display_name(group_key):
    """Retourne le nom d'affichage d'un groupe"""
    return configuration_groupes.get(group_key, {}).get('display_name', group_key)

def get_groups_with_permission(permission_key):
    """Retourne tous les groupes ayant une permission donnée"""
    groups_with_perm = []
    for group_key, group_config in configuration_groupes.items():
        all_perms = group_config.get('django_permissions', [])
        if permission_key in all_perms:
            groups_with_perm.append(group_key)
    return groups_with_perm

def generate_django_permissions_for_model(model_name, actions=['add', 'change', 'delete', 'view']):
    """Génère les permissions Django pour un modèle"""
    return [f'suivi_conducteurs.{action}_{model_name}' for action in actions]

def get_groupes_evaluateurs():
    """Retourne la liste des groupes pouvant évaluer. Retourne une liste de clefs."""
    return [nom for nom, config in configuration_groupes.items() if config.get('evaluer_p', False)]

def get_noms_groupes_autorises():
    """Retourne les noms affichés des groupes pouvant évaluer"""
    return [configuration_groupes[nom]['display_name'] for nom in get_groupes_evaluateurs()]

# ==============================================
# VALIDATION ET HELPERS
# ==============================================

def validate_group_config():
    """Valide la configuration des groupes"""
    errors = []
    
    for group_key, group_config in configuration_groupes.items():
        # Vérifier les champs obligatoires
        required_fields = ['display_name', 'description']
        for field in required_fields:
            if field not in group_config:
                errors.append(f"Groupe {group_key}: champ manquant '{field}'")
    
    return errors

def get_all_available_permissions():
    """Retourne toutes les permissions disponibles """
    django_perms = []
    for model, actions in permissions_modele.items():
        django_perms.extend(generate_django_permissions_for_model(model, actions))
    
    return {'django_permissions': django_perms, }

# ==============================================
# CONFIGURATION POUR L'ADMIN
# ==============================================

ADMIN_CONFIG = {
    'show_permission_summary': True,
    'group_permissions_inline': True,
    'color_code_levels': True,
    'default_group_level': 1
}
