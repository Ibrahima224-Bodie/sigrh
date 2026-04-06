from django.db import migrations


ROLE_GROUP_PREFIX = "ROLE::"


def role_group_name(role_code):
    return f"{ROLE_GROUP_PREFIX}{role_code}"


def create_directeur_role_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model("comptes", "User")

    directeur_group, _ = Group.objects.get_or_create(name=role_group_name("directeur_ecole"))

    conge_permissions = Permission.objects.filter(
        content_type__app_label="absences",
        codename__in=["view_conge", "view_commentaireconge", "add_commentaireconge"],
    )
    directeur_group.permissions.add(*conge_permissions)

    for user in User.objects.filter(role="directeur_ecole"):
        user.groups.add(directeur_group)


def rollback_directeur_role_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=role_group_name("directeur_ecole")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comptes", "0005_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(create_directeur_role_group, rollback_directeur_role_group),
    ]
