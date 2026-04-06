from django.db import models


class AssistantIAAccess(models.Model):
    class Meta:
        verbose_name = 'accès assistant IA'
        verbose_name_plural = 'accès assistant IA'
        default_permissions = ()
        permissions = [
            ('use_ai_assistant', "Peut utiliser l'assistant IA"),
        ]
