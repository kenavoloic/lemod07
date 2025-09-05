# Migration initiale avec données d'initialisation

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

def create_initial_data(apps, schema_editor):
    """Création des données d'initialisation"""
    from datetime import date
    
    # Récupération des modèles
    Site = apps.get_model('suivi_conducteurs', 'Site')
    Societe = apps.get_model('suivi_conducteurs', 'Societe')
    Service = apps.get_model('suivi_conducteurs', 'Service')
    TypologieEvaluation = apps.get_model('suivi_conducteurs', 'TypologieEvaluation')
    CritereEvaluation = apps.get_model('suivi_conducteurs', 'CritereEvaluation')
    Conducteur = apps.get_model('suivi_conducteurs', 'Conducteur')
    
    # Création des sites
    sites_data = [
        {'nom_commune': 'Bordeaux', 'code_postal': '33000'},
        {'nom_commune': 'Arcachon', 'code_postal': '33120'},
        {'nom_commune': 'Libourne', 'code_postal': '33500'},
    ]
    
    sites = {}
    for site_data in sites_data:
        site = Site.objects.create(**site_data)
        sites[site.nom_commune] = site
    
    # Création des sociétés
    societes_data = [
        {
            'socid': 1,
            'socnom': 'BDX Transport',
            'socactif': True,
            'soccode': 'BDX001',
            'soccp': '33000',
            'socvillib1': 'Bordeaux'
        },
        {
            'socid': 2,
            'socnom': 'Bassin Transport',
            'socactif': True,
            'soccode': 'BSN001',
            'soccp': '33120',
            'socvillib1': 'Arcachon'
        },
        {
            'socid': 3,
            'socnom': 'Entre-Deux-Mers Transport',
            'socactif': True,
            'soccode': 'EDM001',
            'soccp': '33500',
            'socvillib1': 'Libourne'
        },
    ]
    
    societes = {}
    for societe_data in societes_data:
        societe = Societe.objects.create(**societe_data)
        societes[societe.socid] = societe
    
    # Création des services
    services_data = [
        {'nom': 'Ressources Humaines', 'abreviation': 'RH'},
        {'nom': 'Exploitation', 'abreviation': 'EXP'},
        {'nom': 'Direction', 'abreviation': 'DIR'},
    ]
    
    for service_data in services_data:
        Service.objects.create(**service_data)
    
    # Création des types d'évaluation
    types_evaluation_data = [
        {
            'nom': 'RH',
            'description': 'Évaluation RH',
            'abreviation': 'RH'
        },
        {
            'nom': 'Exploitation',
            'description': 'Évaluation Exploitation',
            'abreviation': 'EXP'
        },
        {
            'nom': 'Formateur',
            'description': 'Évaluation Conduite',
            'abreviation': 'FORM'
        },
    ]
    
    types_evaluation = {}
    for type_data in types_evaluation_data:
        type_eval = TypologieEvaluation.objects.create(**type_data)
        types_evaluation[type_data['nom']] = type_eval
    
    # Définition des critères par type d'évaluation
    criteres_par_type = {
        'Formateur': [
            'Prise en main du tracteur/porteur',
            'Prise en main de la remorque',
            'Position sur les voies',
            'Trajectoire',
            'Trajectoire courbe',
            'Rond-point',
            'Notions écoconduite',
            'Mise en application des consignes',
            'Manoeuvre',
            'Attelage/dételage',
            'Geste et posture'
        ],
        'Exploitation': [
            'Respect des horaires',
            'Entretien du véhicule',
            'Communication',
            'Respect des horaires de travail (ODM)',
            'Remplissage des CMR',
            'Avis client',
            'Comportement interne'
        ],
        'RH': [
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'
        ]
    }
    
    # Création des critères d'évaluation
    for type_nom, type_eval in types_evaluation.items():
        criteres_liste = criteres_par_type[type_nom]
        
        for critere_nom in criteres_liste:
            CritereEvaluation.objects.create(
                nom=critere_nom,
                type_evaluation=type_eval,
                valeur_mini=1,
                valeur_maxi=10,  # Échelle de 1 à 10
                actif=True  # Tous les critères sont actifs
            )
    
    # Création des conducteurs - 10 par société
    conducteurs_data = {
        1: [  # BDX Transport - Bordeaux
            {'salnom': 'Martin', 'salnom2': 'Pierre', 'date_naissance': date(1985, 3, 15), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Dubois', 'salnom2': 'Jean', 'date_naissance': date(1978, 7, 22), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Bernard', 'salnom2': 'Michel', 'date_naissance': date(1982, 11, 8), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Petit', 'salnom2': 'Alain', 'date_naissance': date(1990, 1, 12), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Robert', 'salnom2': 'François', 'date_naissance': date(1975, 9, 30), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Richard', 'salnom2': 'Philippe', 'date_naissance': date(1988, 5, 18), 'interim_p': False, 'sous_traitant_p': True},
            {'salnom': 'Durand', 'salnom2': 'Antoine', 'date_naissance': date(1983, 12, 4), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Moreau', 'salnom2': 'Stéphane', 'date_naissance': date(1987, 6, 25), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Simon', 'salnom2': 'Christophe', 'date_naissance': date(1981, 4, 14), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Laurent', 'salnom2': 'Thierry', 'date_naissance': date(1979, 10, 7), 'interim_p': False, 'sous_traitant_p': True},
        ],
        2: [  # Bassin Transport - Arcachon
            {'salnom': 'Garcia', 'salnom2': 'Carlos', 'date_naissance': date(1986, 2, 20), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Rodriguez', 'salnom2': 'Manuel', 'date_naissance': date(1984, 8, 16), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Martinez', 'salnom2': 'José', 'date_naissance': date(1977, 12, 28), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Lopez', 'salnom2': 'Miguel', 'date_naissance': date(1991, 3, 9), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Gonzalez', 'salnom2': 'Diego', 'date_naissance': date(1989, 7, 13), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Wilson', 'salnom2': 'David', 'date_naissance': date(1980, 11, 22), 'interim_p': False, 'sous_traitant_p': True},
            {'salnom': 'Anderson', 'salnom2': 'James', 'date_naissance': date(1985, 1, 17), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Taylor', 'salnom2': 'Robert', 'date_naissance': date(1976, 9, 5), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Brown', 'salnom2': 'Michael', 'date_naissance': date(1992, 4, 11), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Davis', 'salnom2': 'William', 'date_naissance': date(1983, 6, 27), 'interim_p': False, 'sous_traitant_p': True},
        ],
        3: [  # Entre-Deux-Mers Transport - Libourne
            {'salnom': 'Leroy', 'salnom2': 'Pascal', 'date_naissance': date(1974, 5, 3), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Roux', 'salnom2': 'Frédéric', 'date_naissance': date(1987, 9, 19), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Vincent', 'salnom2': 'Olivier', 'date_naissance': date(1981, 2, 26), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Fournier', 'salnom2': 'Yves', 'date_naissance': date(1990, 12, 1), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Girard', 'salnom2': 'Patrice', 'date_naissance': date(1978, 8, 24), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Bonnet', 'salnom2': 'Gérard', 'date_naissance': date(1985, 4, 6), 'interim_p': False, 'sous_traitant_p': True},
            {'salnom': 'Dupont', 'salnom2': 'Serge', 'date_naissance': date(1982, 10, 15), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Lambert', 'salnom2': 'Bruno', 'date_naissance': date(1988, 6, 8), 'interim_p': True, 'sous_traitant_p': False},
            {'salnom': 'Fontaine', 'salnom2': 'Claude', 'date_naissance': date(1979, 1, 21), 'interim_p': False, 'sous_traitant_p': False},
            {'salnom': 'Rousseau', 'salnom2': 'Éric', 'date_naissance': date(1986, 11, 12), 'interim_p': False, 'sous_traitant_p': True},
        ]
    }
    
    # Mapping des sociétés vers leurs sites
    societe_site_mapping = {
        1: sites['Bordeaux'],    # BDX Transport -> Bordeaux
        2: sites['Arcachon'],    # Bassin Transport -> Arcachon
        3: sites['Libourne'],    # Entre-Deux-Mers Transport -> Libourne
    }
    
    # Création des conducteurs
    for socid, conducteurs_list in conducteurs_data.items():
        societe = societes[socid]
        site = societe_site_mapping[socid]
        
        for conducteur_data in conducteurs_list:
            Conducteur.objects.create(
                salnom=conducteur_data['salnom'],
                salnom2=conducteur_data['salnom2'],
                salsocid=societe,
                site=site,
                date_naissance=conducteur_data['date_naissance'],
                interim_p=conducteur_data['interim_p'],
                sous_traitant_p=conducteur_data['sous_traitant_p'],
                salactif=True  # Tous actifs par défaut
            )

def reverse_initial_data(apps, schema_editor):
    """Suppression des données d'initialisation en cas de rollback"""
    
    # Récupération des modèles
    Site = apps.get_model('suivi_conducteurs', 'Site')
    Societe = apps.get_model('suivi_conducteurs', 'Societe')
    Service = apps.get_model('suivi_conducteurs', 'Service')
    TypologieEvaluation = apps.get_model('suivi_conducteurs', 'TypologieEvaluation')
    CritereEvaluation = apps.get_model('suivi_conducteurs', 'CritereEvaluation')
    Conducteur = apps.get_model('suivi_conducteurs', 'Conducteur')
    
    # Suppression dans l'ordre inverse des dépendances
    Conducteur.objects.all().delete()
    CritereEvaluation.objects.all().delete()
    TypologieEvaluation.objects.all().delete()
    Service.objects.all().delete()
    Societe.objects.all().delete()
    Site.objects.all().delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # Création du modèle Site
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_commune', models.CharField(max_length=255, verbose_name='Commune')),
                ('code_postal', models.CharField(max_length=5, validators=[django.core.validators.RegexValidator(message='Un code postal est long de 5 caractères', regex='^\\d{5}$')], verbose_name='Code postal')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Site',
                'verbose_name_plural': 'Sites',
                'ordering': ['nom_commune'],
            },
        ),
        
        # Création du modèle Societe
        migrations.CreateModel(
            name='Societe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('socid', models.PositiveIntegerField(unique=True)),
                ('socnom', models.CharField(max_length=255, verbose_name='Nom société')),
                ('socactif', models.BooleanField(default=True, verbose_name='Active')),
                ('soccode', models.CharField(max_length=255, verbose_name='Code société')),
                ('soccp', models.CharField(max_length=5, validators=[django.core.validators.RegexValidator(message='Un code postal est long de 5 caractères', regex='^\\d{5}$')], verbose_name='Code postal')),
                ('socvillib1', models.CharField(max_length=255, verbose_name='Ville')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Société',
                'verbose_name_plural': 'Sociétés',
                'ordering': ['socnom'],
                'indexes': [models.Index(fields=['socnom'], name='suivi_conducteurs_societe_socnom_idx')],
            },
        ),
        
        # Création du modèle Service
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, verbose_name='Nom du service')),
                ('abreviation', models.CharField(max_length=10, verbose_name='Abréviation')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Service',
                'verbose_name_plural': 'Services',
                'ordering': ['nom'],
            },
        ),
        
        # Création du modèle TypologieEvaluation
        migrations.CreateModel(
            name='TypologieEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, verbose_name='Nom')),
                ('abreviation', models.CharField(max_length=10, verbose_name='Abréviation')),
                ('description', models.TextField(verbose_name='Description')),
            ],
            options={
                'verbose_name': "Type d'évaluation",
                'verbose_name_plural': "Types d'évaluation",
            },
        ),
        
        # Création du modèle Conducteur
        migrations.CreateModel(
            name='Conducteur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('salnom', models.CharField(max_length=255, verbose_name='nom')),
                ('salnom2', models.CharField(max_length=255, verbose_name='prénom')),
                ('salactif', models.BooleanField(default=True, verbose_name='Conducteur actif')),
                ('interim_p', models.BooleanField(default=True, verbose_name='Intérim')),
                ('sous_traitant_p', models.BooleanField(default=True, verbose_name='Sous-traitant')),
                ('date_naissance', models.DateField(blank=True, null=True, verbose_name='Date de naissance')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('salsocid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.societe', to_field='socid', verbose_name='Société')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.site', verbose_name='Site')),
            ],
            options={
                'verbose_name': 'Conducteur',
                'verbose_name_plural': 'Conducteurs',
                'ordering': ['salnom', 'salnom2'],
            },
        ),
        
        # Création du modèle Evaluateur
        migrations.CreateModel(
            name='Evaluateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, verbose_name='nom')),
                ('prenom', models.CharField(max_length=255, verbose_name='prénom')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.service', verbose_name='Service')),
            ],
            options={
                'verbose_name': 'Évaluateur',
                'verbose_name_plural': 'Évaluateurs',
                'ordering': ['nom', 'prenom'],
            },
        ),
        
        # Création du modèle CritereEvaluation
        migrations.CreateModel(
            name='CritereEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('valeur_mini', models.PositiveIntegerField()),
                ('valeur_maxi', models.PositiveIntegerField()),
                ('actif', models.BooleanField(default=True, help_text='Critère actuellement utilisé')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('type_evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.typologieevaluation')),
            ],
            options={
                'verbose_name': "Critère d'évaluation",
                'verbose_name_plural': "Critères d'évaluation",
                'ordering': ['numero_ordre'],
            },
        ),
        
        # Création du modèle Evaluation
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_evaluation', models.DateField(verbose_name="Date d'évaluation")),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('conducteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.conducteur', verbose_name='Conducteur')),
                ('evaluateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.evaluateur', verbose_name='Évaluateur')),
                ('type_evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.typologieevaluation', verbose_name="Type d'évaluation")),
            ],
            options={
                'verbose_name': 'Évaluation',
                'verbose_name_plural': 'Évaluations',
                'ordering': ['-date_evaluation'],
                'indexes': [
                    models.Index(fields=['date_evaluation'], name='suivi_conducteurs_evaluation_date_idx'),
                    models.Index(fields=['conducteur'], name='suivi_conducteurs_evaluation_conducteur_idx'),
                    models.Index(fields=['type_evaluation'], name='suivi_conducteurs_evaluation_type_idx'),
                ],
            },
        ),
        
        # Création du modèle Note
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valeur', models.PositiveIntegerField(blank=True, help_text='Note attribuée', null=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('critere', models.ForeignKey(help_text='Critère évalué', on_delete=django.db.models.deletion.CASCADE, to='suivi_conducteurs.critereevaluation')),
                ('evaluation', models.ForeignKey(help_text="Session d'évaluation", on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='suivi_conducteurs.evaluation')),
            ],
            options={
                'verbose_name': 'Note',
                'verbose_name_plural': 'Notes',
                'ordering': ['critere__numero_ordre'],
                'indexes': [
                    models.Index(fields=['evaluation', 'critere'], name='suivi_conducteurs_note_eval_critere_idx'),
                ],
            },
        ),
        
        # Ajout des contraintes d'unicité
        migrations.AddConstraint(
            model_name='evaluation',
            constraint=models.UniqueConstraint(fields=('conducteur', 'date_evaluation', 'evaluateur', 'type_evaluation'), name='unique_evaluation'),
        ),
        migrations.AddConstraint(
            model_name='note',
            constraint=models.UniqueConstraint(fields=('evaluation', 'critere'), name='unique_note_evaluation_critere'),
        ),
        
        # Migration de données pour créer les données d'initialisation
        migrations.RunPython(
            create_initial_data,
            reverse_initial_data,
        ),
    ]
