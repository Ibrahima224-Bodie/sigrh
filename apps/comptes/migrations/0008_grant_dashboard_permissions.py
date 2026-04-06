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


def grant_dashboard_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    dashboard_permissions = list(
        Permission.objects.filter(
            content_type__app_label='dashboard',
            codename__in=['access_dashboard', 'use_dashboard_chatbot'],
        )
    )
    if not dashboard_permissions:
        return

    for role_code, _ in ROLE_CHOICES:
        group, _ = Group.objects.get_or_create(name=role_group_name(role_code))
        group.permissions.add(*dashboard_permissions)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
        ('comptes', '0007_sync_role_group_permissions'),
    ]

    operations = [
        migrations.RunPython(grant_dashboard_permissions, noop_reverse),
    ]