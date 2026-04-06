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


def grant_dashboard_stats_permission(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    dashboard_stats_permission = Permission.objects.filter(
        content_type__app_label='dashboard',
        codename='view_dashboard_statistics',
    ).first()

    if dashboard_stats_permission is None:
        return

    for role_code, _ in ROLE_CHOICES:
        group, _ = Group.objects.get_or_create(name=role_group_name(role_code))
        group.permissions.add(dashboard_stats_permission)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_dashboardaccess_options'),
        ('comptes', '0008_grant_dashboard_permissions'),
    ]

    operations = [
        migrations.RunPython(grant_dashboard_stats_permission, noop_reverse),
    ]
