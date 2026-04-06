from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AssistantIAAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'accès assistant IA',
                'verbose_name_plural': 'accès assistant IA',
                'default_permissions': (),
                'permissions': [
                    ('use_ai_assistant', "Peut utiliser l'assistant IA"),
                ],
            },
        ),
    ]
