from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from gestion_groupes.config import configuration_groupes
from gestion_groupes.models import GroupeEtendu


class Command(BaseCommand):
    help = 'Synchronise les permissions des groupes selon gestion_groupes/config.py'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )
        parser.add_argument(
            '--group',
            type=str,
            help='Synchroniser seulement un groupe spécifique',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_group = options['group']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN: Aucune modification ne sera appliquée\n')
            )

        # Récupérer tous les groupes à traiter
        groups_to_process = configuration_groupes.keys()
        if specific_group:
            if specific_group not in configuration_groupes:
                self.stdout.write(
                    self.style.ERROR(f'Groupe "{specific_group}" non trouvé dans la configuration')
                )
                return
            groups_to_process = [specific_group]

        # Traiter chaque groupe
        for group_name in groups_to_process:
            self.sync_group_permissions(group_name, dry_run)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Synchronisation terminée avec succès!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n💡 Pour appliquer les changements, exécutez sans --dry-run')
            )

    def sync_group_permissions(self, group_name, dry_run=False):
        """Synchronise les permissions d'un groupe selon la configuration"""
        config = configuration_groupes[group_name]
        
        self.stdout.write(f'\n📋 Traitement du groupe: {group_name}')
        self.stdout.write(f'   Description: {config.get("description", "N/A")}')
        
        # Récupérer ou créer le groupe Django
        try:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'   ✨ Groupe Django créé: {group_name}')
            else:
                self.stdout.write(f'   📌 Groupe Django existant: {group_name}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erreur lors de la création du groupe: {e}')
            )
            return

        # Récupérer ou créer le GroupeEtendu
        try:
            groupe_etendu, created = GroupeEtendu.objects.get_or_create(
                group=group,
                defaults={
                    'description': config.get('description', ''),
                    'couleur': config.get('color', '#6c757d'),
                    'niveau_acces': config.get('level', 1),
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'   ✨ GroupeEtendu créé')
            else:
                # Mettre à jour les informations existantes
                groupe_etendu.description = config.get('description', groupe_etendu.description)
                groupe_etendu.couleur = config.get('color', groupe_etendu.couleur)
                groupe_etendu.niveau_acces = config.get('level', groupe_etendu.niveau_acces)
                if not dry_run:
                    groupe_etendu.save()
                self.stdout.write(f'   📝 GroupeEtendu mis à jour')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erreur lors de la gestion du GroupeEtendu: {e}')
            )

        # Traiter les permissions Django
        django_permissions = config.get('django_permissions', [])
        
        if not django_permissions:
            self.stdout.write(f'   ⚠️  Aucune permission définie dans la configuration')
            return

        # Récupérer les permissions actuelles du groupe
        current_permissions = set(group.permissions.values_list('codename', 'content_type__app_label'))
        current_perm_names = {f"{app}.{codename}" for codename, app in current_permissions}

        # Convertir la configuration en permissions Django
        target_permissions = set()
        permissions_to_add = []
        
        for perm_name in django_permissions:
            try:
                app_label, codename = perm_name.split('.', 1)
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=app_label
                )
                target_permissions.add(perm_name)
                permissions_to_add.append(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  Permission introuvable: {perm_name}')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Format de permission invalide: {perm_name}')
                )

        # Calculer les changements
        to_add = target_permissions - current_perm_names
        to_remove = current_perm_names - target_permissions

        # Afficher les changements
        if to_add:
            self.stdout.write(f'   ➕ Permissions à ajouter ({len(to_add)}):')
            for perm in sorted(to_add):
                self.stdout.write(f'      • {perm}')

        if to_remove:
            self.stdout.write(f'   ➖ Permissions à supprimer ({len(to_remove)}):')
            for perm in sorted(to_remove):
                self.stdout.write(f'      • {perm}')

        if not to_add and not to_remove:
            self.stdout.write(f'   ✅ Permissions déjà synchronisées')
            return

        # Appliquer les changements si pas en dry-run
        if not dry_run:
            try:
                # Supprimer les permissions obsolètes
                if to_remove:
                    perms_to_remove = Permission.objects.filter(
                        codename__in=[perm.split('.', 1)[1] for perm in to_remove],
                        content_type__app_label__in=[perm.split('.', 1)[0] for perm in to_remove]
                    )
                    group.permissions.remove(*perms_to_remove)

                # Ajouter les nouvelles permissions
                if to_add:
                    perms_to_add = Permission.objects.filter(
                        codename__in=[perm.split('.', 1)[1] for perm in to_add],
                        content_type__app_label__in=[perm.split('.', 1)[0] for perm in to_add]
                    )
                    group.permissions.add(*perms_to_add)

                self.stdout.write(f'   ✅ Permissions synchronisées avec succès')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Erreur lors de la synchronisation: {e}')
                )
        
        # Afficher le résumé final
        final_count = len(target_permissions)
        self.stdout.write(f'   📊 Total des permissions configurées: {final_count}')