from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dashboardaccess',
            options={
                'verbose_name': 'accès tableau de bord',
                'verbose_name_plural': 'accès tableau de bord',
                'default_permissions': (),
                'permissions': [
                    ('access_dashboard', 'Peut accéder au tableau de bord'),
                    ('view_dashboard_statistics', 'Peut voir les statistiques du tableau de bord'),
                    ('use_dashboard_chatbot', "Peut utiliser l'assistant du tableau de bord"),
                ],
            },
        ),
    ]
