from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.urls import path, reverse
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .services import calcular_classificacao
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
Partida,
)
admin.site.register(Cidade)
admin.site.register(Modalidade)
admin.site.register(Categoria)
admin.site.register(Equipe)
admin.site.register(Jogador)
admin.site.register(JogadorEquipe)
admin.site.register(InscricaoEquipe)
admin.site.register(InscricaoJogador)

@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):

    list_display = (
        'campeonato',
        'equipe_mandante',
        'placar',
        'equipe_visitante',
        'data',
        'horario',
        'local',
        'status',
        'exibir_resultado',
    )

    list_filter = (
        'campeonato',
        'status',
        'data',
    )

    search_fields = (
        'equipe_mandante__equipe__nome',
        'equipe_visitante__equipe__nome',
        'local',
    )
    
    ordering = ('data', 'horario')

    @admin.display(description='Placar')
    def placar(self, obj):
        if obj.gols_mandante is None or obj.gols_visitante is None:
            return '-'

        return f'{obj.gols_mandante} x {obj.gols_visitante}'

    @admin.display(description='Resultado')
    def exibir_resultado(self, obj):
        resultado = obj.resultado()

        if resultado == 'mandante':
            return f'Vitória de {obj.equipe_mandante.equipe}'

        elif resultado == 'visitante':
            return f'Vitória de {obj.equipe_visitante.equipe}'

        elif resultado == 'empate':
            return 'Empate'

        return '-'

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
            groups__in=Group.objects.exclude(name='Organizador')
        ).exclude(
            user_permissions__isnull=False
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

            if not request.user.groups.filter(
                name='Administrador'
            ).exists():
                return False
            
            if obj is not None:
                if not self.get_queryset(request).filter(
                    pk=obj.pk
                ).exists():
                    return False

        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):

        if not request.user.is_superuser:
            if not request.user.groups.filter(
                name='Administrador'
            ).exists():
                return False
        
        return super().has_add_permission(request)

    def lookup_allowed(self, lookup, value, request=None):
        if request is not None and not request.user.is_superuser:
            if lookup.startswith(('groups', 'user_permissions')):
                return False

        return super().lookup_allowed(
            lookup, value, request=request
        )

@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'modalidade',
        'categoria',
        'cidade',
        'status',
        'visualizar_classificacao',
    )

    @admin.display(description='Classificação')
    def visualizar_classificacao(self, obj):
        url = reverse(
            'admin:campeonato_classificacao',
            args=[obj.pk]
        )

        return format_html(
            '<a class="button" href="{}">Visualizar classificação</a>',
            url
        )

    def get_urls(self):
        urls = super().get_urls()

        novas_urls = [
            path(
                '<int:campeonato_id>/classificacao/',
                self.admin_site.admin_view(self.classificacao),
                name='campeonato_classificacao'
            ),
        ]

        return novas_urls + urls
    
    def classificacao(self, request, campeonato_id):

        campeonato = self.get_object(request, str(campeonato_id))

        if campeonato is None:
            raise Http404('Campeonato não encontrado.')
        
        if not self.has_view_or_change_permission(request, campeonato):
            raise PermissionDenied

        tabela = calcular_classificacao(campeonato)

        contexto = {
            **self.admin_site.each_context(request),
            'title': f'Classificação - {campeonato.nome}',
            'campeonato': campeonato,
            'tabela': tabela,
            'opts': self.model._meta,
        }

        return TemplateResponse(
            request,
            'classificacao.html',
            contexto
        )