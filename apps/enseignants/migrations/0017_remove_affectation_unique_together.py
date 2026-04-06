from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enseignants', '0016_alter_programme_filiere_nullable'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='affectation',
            unique_together=set(),
        ),
    ]