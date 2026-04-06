from django.db import migrations

OLD_MODULE_PERMS = [
    'access_geo_filters',
    'filter_filieres_by_etablissement',
    'preview_affectation',
    'export_csv_template',
    'export_csv_data',
    'import_csv_data',
]


def remove_old_module_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    try:
        ct = ContentType.objects.get(app_label='enseignants', model='module')
    except ContentType.DoesNotExist:
        return
    Permission.objects.filter(content_type=ct, codename__in=OLD_MODULE_PERMS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('enseignants', '0023_add_per_entity_csv_and_semantic_perms'),
    ]

    operations = [
        migrations.RunPython(remove_old_module_permissions, migrations.RunPython.noop),
    ]
