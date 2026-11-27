from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.db import transaction


class Command(BaseCommand):
    help = 'Configura os grupos e permissões do Hat Trick'

    @transaction.atomic
    def handle(self, *args, **options):

        modelos = [
            'cidade',
            'modalidade',
            'categoria',
            'campeonato',
            'equipe',
            'jogador',
            'jogadorequipe',
            'inscricaoequipe',
            'inscricaojogador',
            'partida',
            'estatisticapartida',
        ]

        acoes = ['add', 'change', 'delete', 'view']

        codigos = [
            f'{acao}_{modelo}'
            for modelo in modelos
            for acao in acoes
        ]

        permissoes = Permission.objects.filter(
            content_type__app_label='campeonatos',
            codename__in=codigos
        )

        if permissoes.count() != len(codigos):
            raise CommandError(
                'Permissões não encontradas. Verifique as migrações.'
            )

        # Grupo Organizador
        organizador, _ = Group.objects.get_or_create(
            name='Organizador'
        )

        organizador.permissions.set(permissoes)

        # Grupo Administrador
        administrador, _ = Group.objects.get_or_create(
            name='Administrador'
        )

        permissoes_usuarios = Permission.objects.filter(
            content_type__app_label='auth',
            content_type__model='user',
            codename__in=[
                'add_user',
                'change_user',
                'view_user',
            ]
        )

                # Grupo Visitante
        visitante, _ = Group.objects.get_or_create(
            name='Visitante'
        )

        visitante.permissions.clear()
        administrador.permissions.set(permissoes)
        administrador.permissions.add(*permissoes_usuarios)

        self.stdout.write(
            self.style.SUCCESS(
                'Grupos e permissões configurados com sucesso!'
            )
        )