from django.db import migrations


ROLE_GROUP_PREFIX = "ROLE::"
ROLE_CHOICES = [
    ("administrateur", "Administrateur"),
    ("chef_service_drh", "Chef service DRH"),
    ("secretaire_general", "Secretaire general"),
    ("chef_cabinet", "Chef de cabinet"),
    ("ministre", "Ministre"),
    ("technicien_drh", "Technicien DRH"),
    ("professeur", "Professeur"),
]


def role_group_name(role_code):
    return f"{ROLE_GROUP_PREFIX}{role_code}"


def bootstrap_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model("comptes", "User")

    groups = {}
    for role_code, _ in ROLE_CHOICES:
        group, created = Group.objects.get_or_create(name=role_group_name(role_code))
        groups[role_code] = group

    all_permissions = Permission.objects.all()
    hr_permissions = Permission.objects.filter(content_type__app_label="enseignants")
    user_permissions = Permission.objects.filter(content_type__app_label="comptes", content_type__model="user")
    auth_permissions = Permission.objects.filter(content_type__app_label="auth", content_type__model__in=["group", "permission"])

    groups["administrateur"].permissions.set(all_permissions)
    shared_admin_permissions = list(hr_permissions) + list(user_permissions) + list(auth_permissions)
    groups["chef_service_drh"].permissions.set(shared_admin_permissions)
    groups["technicien_drh"].permissions.set(shared_admin_permissions)

    role_group_names = [role_group_name(role_code) for role_code, _ in ROLE_CHOICES]
    for user in User.objects.all():
        user.groups.remove(*Group.objects.filter(name__in=role_group_names))
        if user.role in groups:
            user.groups.add(groups[user.role])


def rollback_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    role_group_names = [role_group_name(role_code) for role_code, _ in ROLE_CHOICES]
    Group.objects.filter(name__in=role_group_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comptes", "0002_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(bootstrap_role_groups, rollback_role_groups),
    ]