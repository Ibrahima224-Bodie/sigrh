from django.db import migrations


ROLE_GROUP_PREFIX = 'ROLE::'
ROLE_CHOICES = [
    ('administrateur', 'Administrateur'),
    ('directeur_ecole', "Directeur d'ecole"),
    ('chef_service_drh', 'Chef service DRH'),
    ('secretaire_general', 'Secretaire general'),
    ('chef_cabinet', 'Chef de cabinet'),
    ('ministre', 'Ministre'),
    ('technicien_drh', 'Technicien DRH'),
    ('agent', 'Agent'),
    ('professeur', 'Professeur'),
]


def role_group_name(role_code):
    return f'{ROLE_GROUP_PREFIX}{role_code}'


def split_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    dashboard_codenames = [
        'access_dashboard',
        'view_dashboard_agents_section',
        'view_dashboard_formations_section',
        'view_dashboard_professeurs_section',
        'view_dashboard_filieres_section',
        'view_dashboard_programmes_section',
        'view_dashboard_modules_section',
        'view_dashboard_etablissements_section',
        'view_dashboard_conges_section',
        'view_dashboard_carrieres_section',
    ]

    dashboard_permissions = list(
        Permission.objects.filter(
            content_type__app_label='dashboard',
            codename__in=dashboard_codenames,
        )
    )

    assistant_permission = Permission.objects.filter(
        content_type__app_label='assistant_ia',
        codename='use_ai_assistant',
    ).first()

    legacy_permissions = list(
        Permission.objects.filter(
            content_type__app_label='dashboard',
            codename__in=['use_dashboard_chatbot', 'view_dashboard_statistics'],
        )
    )

    for role_code, _ in ROLE_CHOICES:
        group, _ = Group.objects.get_or_create(name=role_group_name(role_code))
        if dashboard_permissions:
            group.permissions.add(*dashboard_permissions)
        if assistant_permission is not None:
            group.permissions.add(assistant_permission)
        if legacy_permissions:
            group.permissions.remove(*legacy_permissions)

    if legacy_permissions:
        Permission.objects.filter(id__in=[p.id for p in legacy_permissions]).delete()


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('assistant_ia', '0001_initial'),
        ('dashboard', '0003_alter_dashboardaccess_options'),
        ('comptes', '0009_grant_dashboard_stats_permission'),
    ]

    operations = [
        migrations.RunPython(split_permissions, noop_reverse),
    ]
