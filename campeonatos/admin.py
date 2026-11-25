from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from .models import (
Cidade, 
Modalidade,
Categoria, 
Campeonato, 
Equipe, 
Jogador,
JogadorEquipe,
InscricaoEquipe,
InscricaoJogador,
)
admin.site.register(Cidade)
admin.site.register(Modalidade)
admin.site.register(Categoria)
admin.site.register(Campeonato)
admin.site.register(Equipe)
admin.site.register(Jogador)
admin.site.register(JogadorEquipe)
admin.site.register(InscricaoEquipe)
admin.site.register(InscricaoJogador)

admin.site.unregister(User)

@admin.register(User)
class UsuarioAdmin(UserAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(
            groups__name='Organizador',
            is_superuser=False
        ).exclude(
            groups__name='Administrador'
        ).distinct()

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)

        if obj is None:
            return self.add_fieldsets

        return (
            (None, {
                'fields': ('username',)
            }),
            ('Informações Pessoais', {
                'fields': ('first_name', 'last_name', 'email')
            }),
            ('Situação', {
                'fields': ('is_active',)
            }),
        )

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.is_superuser = False
            obj.is_staff = True

        super().save_model(request, obj, form, change)

        if not request.user.is_superuser:
            grupo = Group.objects.get(name='Organizador')
            obj.groups.set([grupo])
            obj.user_permissions.clear()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if not request.user.is_superuser:
            if obj is not None:
                if obj.is_superuser or obj.groups.filter(
                    name='Administrador'
                ).exists():
                    return False

        return super().has_change_permission(request, obj)


    def lookup_allowed(self, lookup, value, request=None):
        if request is not None and not request.user.is_superuser:
            if lookup.startswith(('groups', 'user_permissions')):
                return False

        return super().lookup_allowed(
            lookup, value, request=request
        )