from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DashboardAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'accès tableau de bord',
                'verbose_name_plural': 'accès tableau de bord',
                'default_permissions': (),
                'permissions': [
                    ('access_dashboard', 'Peut accéder au tableau de bord'),
                    ('use_dashboard_chatbot', "Peut utiliser l'assistant du tableau de bord"),
                ],
            },
        ),
    ]