import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0001_initial'),
        ('enseignants', '0014_alter_secteur_unique_together'),
        ('absences', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conge',
            name='agent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conges', to='agents.agent'),
        ),
        migrations.AddField(
            model_name='conge',
            name='professeur',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conges', to='enseignants.professeur'),
        ),
    ]