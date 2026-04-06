from django.db import migrations, models


def delete_orphan_secteurs(apps, schema_editor):
    Secteur = apps.get_model('enseignants', 'Secteur')
    Secteur.objects.filter(quartier__isnull=True).delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('enseignants', '0012_alter_professeur_statut_alter_secteur_quartier'),
    ]

    operations = [
        migrations.RunPython(delete_orphan_secteurs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='secteur',
            name='quartier',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='secteurs', to='enseignants.quartier'),
        ),
    ]
