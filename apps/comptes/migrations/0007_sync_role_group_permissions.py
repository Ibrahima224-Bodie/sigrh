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


def ensure_group_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    User = apps.get_model('comptes', 'User')

    groups = {}
    for role_code, _ in ROLE_CHOICES:
        group, _ = Group.objects.get_or_create(name=role_group_name(role_code))
        groups[role_code] = group

    all_permissions = list(Permission.objects.all())
    enseignants_permissions = list(Permission.objects.filter(content_type__app_label='enseignants'))
    absences_permissions = list(Permission.objects.filter(content_type__app_label='absences'))
    comptes_user_permissions = list(
        Permission.objects.filter(content_type__app_label='comptes', content_type__model='user')
    )
    auth_permissions = list(
        Permission.objects.filter(content_type__app_label='auth', content_type__model__in=['group', 'permission'])
    )

    demander_conge_permissions = list(
        Permission.objects.filter(content_type__app_label='absences', codename='demander_conge')
    )
    directeur_conge_permissions = list(
        Permission.objects.filter(
            content_type__app_label='absences',
            codename__in=[
                'view_conge',
                'view_commentaireconge',
                'add_commentaireconge',
                'approuver_conge_directeur',
            ],
        )
    )
    drh_conge_permissions = list(
        Permission.objects.filter(
            content_type__app_label='absences',
            codename__in=[
                'view_conge',
                'change_conge',
                'view_commentaireconge',
                'add_commentaireconge',
                'approuver_conge_directeur',
                'valider_conge_drh',
            ],
        )
    )

    groups['administrateur'].permissions.add(*all_permissions)
    groups['chef_service_drh'].permissions.add(
        *(enseignants_permissions + absences_permissions + comptes_user_permissions + auth_permissions)
    )
    groups['technicien_drh'].permissions.add(
        *(enseignants_permissions + absences_permissions + comptes_user_permissions + auth_permissions)
    )
    groups['directeur_ecole'].permissions.add(*directeur_conge_permissions)
    groups['agent'].permissions.add(*demander_conge_permissions)
    groups['professeur'].permissions.add(*demander_conge_permissions)

    role_group_names = [role_group_name(role_code) for role_code, _ in ROLE_CHOICES]
    role_groups = Group.objects.filter(name__in=role_group_names)
    for user in User.objects.all():
        user.groups.remove(*role_groups)
        target_group = groups.get(user.role)
        if target_group is not None:
            user.groups.add(target_group)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('absences', '0006_alter_conge_options'),
        ('comptes', '0006_directeur_role_group'),
    ]

    operations = [
        migrations.RunPython(ensure_group_permissions, noop_reverse),
    ]