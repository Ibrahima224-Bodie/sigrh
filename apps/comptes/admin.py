from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('structure', 'role', 'photo')}),
    )
    list_display = ('username', 'email', 'role', 'structure', 'is_staff')

admin.site.register(User, CustomUserAdmin)