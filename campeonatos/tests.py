from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.urls import reverse
from datetime import date, time
from datetime import datetime
from unittest.mock import patch
from django.utils import timezone
from .services import calcular_classificacao, separar_partidas
from django.core.exceptions import ValidationError
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

class PermissoesTest(TestCase):

    def setUp(self):
        call_command('configurarGrupos')

        self.superusuario = User.objects.create_superuser(
            username='superusuario_teste',
            password='SenhaTeste123!'
        )

        self.administrador = User.objects.create_user(
            username='administrador_teste',
            password='SenhaTeste123!',
            is_staff=True
        )

        self.organizador = User.objects.create_user(
            username='organizador_teste',
            password='SenhaTeste123!',
            is_staff=True
        )

        self.administrador.groups.add(
            Group.objects.get(name='Administrador')
        )

        self.organizador.groups.add(
            Group.objects.get(name='Organizador')
        )

    def test_organizador_sem_acesso_a_usuarios(self):
        self.client.force_login(self.organizador)

        resposta = self.client.get(
            reverse('admin:auth_user_changelist')
        )

        self.assertEqual(resposta.status_code, 403)

    def test_administrador_pode_cadastrar_usuario(self):
        self.client.force_login(self.administrador)

        resposta = self.client.get(
            reverse('admin:auth_user_add')
        )

        self.assertEqual(resposta.status_code, 200)

    def test_administrador_nao_altera_senha_superusuario(self):
        self.client.force_login(self.administrador)

        resposta = self.client.get(
            reverse(
                'admin:auth_user_password_change',
                args=[self.superusuario.pk]
            )
        )

        self.assertIn(resposta.status_code, [403, 404])

    def test_administrador_nao_exclui_organizador(self):
        self.client.force_login(self.administrador)

        resposta = self.client.get(
            reverse(
                'admin:auth_user_delete',
                args=[self.organizador.pk]
            )
        )

        self.assertEqual(resposta.status_code, 403)

class CampeonatoBaseTest(TestCase):

    def setUp(self):

        self.cidade = Cidade.objects.create(
            nome='Muzambinho',
            uf='MG'
        )

        self.modalidade = Modalidade.objects.create(
            nome='Futsal'
        )

        self.categoria = Categoria.objects.create(
            nome='Sub-17',
            idade_maxima=16
        )

        self.campeonato = Campeonato.objects.create(
            nome='Campeonato Teste',
            modalidade=self.modalidade,
            categoria=self.categoria,
            cidade=self.cidade,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31)
        )

        self.equipe1 = Equipe.objects.create(
            nome='Scorpions',
            cidade=self.cidade
        )

        self.equipe2 = Equipe.objects.create(
            nome='Cortinas',
            cidade=self.cidade
        )

        self.inscricao1 = InscricaoEquipe.objects.create(
            equipe=self.equipe1,
            campeonato=self.campeonato,
            status='aprovada'
        )

        self.inscricao2 = InscricaoEquipe.objects.create(
            equipe=self.equipe2,
            campeonato=self.campeonato,
            status='aprovada'
        )

class CampeonatoTest(CampeonatoBaseTest):

    def test_datas_invalidas(self):
        self.campeonato.data_fim = date(2025, 12, 31)

        with self.assertRaises(ValidationError):
            self.campeonato.save()

    def test_datas_iguais(self):
        self.campeonato.data_fim = self.campeonato.data_inicio

        self.campeonato.save()

        self.assertEqual(
            self.campeonato.data_inicio,
            self.campeonato.data_fim
        )

    def test_jogador_elegivel(self):
        jogador = Jogador.objects.create(
            nome='João',
            cpf='11111111111',
            data_nascimento=date(2010, 5, 10)
        )

        self.assertTrue(
            self.campeonato.jogador_elegivel(jogador)
        )

    def test_jogador_nao_elegivel(self):
        jogador = Jogador.objects.create(
            nome='Pedro',
            cpf='22222222222',
            data_nascimento=date(2008, 5, 10)
        )

        self.assertFalse(
            self.campeonato.jogador_elegivel(jogador)
        )

    def test_inscricao_jogador_equipe_pendente(self):
        self.inscricao1.status = 'pendente'
        self.inscricao1.save()

        jogador = Jogador.objects.create(
            nome='Carlos',
            cpf='33333333333',
            data_nascimento=date(2010, 1, 1)
        )

        vinculo = JogadorEquipe.objects.create(
            jogador=jogador,
            equipe=self.equipe1,
            data_entrada=date(2025, 12, 1)
        )

        with self.assertRaises(ValidationError):
            InscricaoJogador.objects.create(
                jogador_equipe=vinculo,
                inscricao_equipe=self.inscricao1
            )

    def test_cancelamento_inscricao_com_partida(self):
        Partida.objects.create(
            campeonato=self.campeonato,
            equipe_mandante=self.inscricao1,
            equipe_visitante=self.inscricao2,
            data=date(2026, 6, 10),
            horario=time(19, 0),
            local='Ginásio Municipal'
        )

        self.inscricao1.status = 'cancelada'

        with self.assertRaises(ValidationError):
            self.inscricao1.save()

class PartidaTest(CampeonatoBaseTest):

    def criar_partida(self, **kwargs):

        dados = {
            'campeonato': self.campeonato,
            'equipe_mandante': self.inscricao1,
            'equipe_visitante': self.inscricao2,
            'data': date(2026, 6, 10),
            'horario': time(19, 0),
            'local': 'Ginásio Municipal',
            'status': 'agendada',
        }

        dados.update(kwargs)

        return Partida.objects.create(**dados)

    def test_partida_valida(self):
        partida = self.criar_partida()

        self.assertIsNotNone(partida.pk)

    def test_equipes_iguais(self):
        with self.assertRaises(ValidationError):
            self.criar_partida(
                equipe_visitante=self.inscricao1
            )

    def test_partida_fora_do_periodo(self):
        with self.assertRaises(ValidationError):
            self.criar_partida(
                data=date(2027, 1, 1)
            )

    def test_equipe_pendente(self):
        self.inscricao2.status = 'pendente'
        self.inscricao2.save()

        with self.assertRaises(ValidationError):
            self.criar_partida()

    def test_vitoria_mandante(self):
        partida = self.criar_partida(
            status='realizada',
            gols_mandante=3,
            gols_visitante=1
        )

        self.assertEqual(partida.resultado(), 'mandante')

    def test_vitoria_visitante(self):
        partida = self.criar_partida(
            status='realizada',
            gols_mandante=1,
            gols_visitante=3
        )

        self.assertEqual(partida.resultado(), 'visitante')

    def test_empate(self):
        partida = self.criar_partida(
            status='realizada',
            gols_mandante=0,
            gols_visitante=0
        )

        self.assertEqual(partida.resultado(), 'empate')

    def test_placar_negativo(self):
        with self.assertRaises(ValidationError):
            self.criar_partida(
                status='realizada',
                gols_mandante=-1,
                gols_visitante=2
            )

    def test_partida_realizada_sem_placar(self):
        with self.assertRaises(ValidationError):
            self.criar_partida(status='realizada')

    def test_partida_agendada_com_placar(self):
        with self.assertRaises(ValidationError):
            self.criar_partida(
                gols_mandante=2,
                gols_visitante=1
            )

class ClassificacaoConsultaTest(CampeonatoBaseTest):

    def criar_partida(self, **kwargs):

        dados = {
            'campeonato': self.campeonato,
            'equipe_mandante': self.inscricao1,
            'equipe_visitante': self.inscricao2,
            'data': date(2026, 6, 10),
            'horario': time(19, 0),
            'local': 'Ginásio Municipal',
            'status': 'agendada',
        }

        dados.update(kwargs)

        return Partida.objects.create(**dados)

    def test_classificacao_sem_partidas(self):
        tabela = calcular_classificacao(self.campeonato)

        self.assertEqual(len(tabela), 2)

        for equipe in tabela:
            self.assertEqual(equipe['pontos'], 0)
            self.assertEqual(equipe['jogos'], 0)

        self.assertEqual(tabela[0]['equipe'], self.equipe2)

    def test_classificacao_com_vitoria(self):
        self.criar_partida(
            status='realizada',
            gols_mandante=3,
            gols_visitante=1
        )

        tabela = calcular_classificacao(self.campeonato)

        self.assertEqual(tabela[0]['equipe'], self.equipe1)
        self.assertEqual(tabela[0]['pontos'], 3)
        self.assertEqual(tabela[0]['vitorias'], 1)
        self.assertEqual(tabela[0]['saldo_gols'], 2)

        self.assertEqual(tabela[1]['pontos'], 0)
        self.assertEqual(tabela[1]['derrotas'], 1)
        self.assertEqual(tabela[1]['saldo_gols'], -2)

    def test_classificacao_com_empate(self):
        self.criar_partida(
            status='realizada',
            gols_mandante=2,
            gols_visitante=2
        )

        tabela = calcular_classificacao(self.campeonato)

        for equipe in tabela:
            self.assertEqual(equipe['pontos'], 1)
            self.assertEqual(equipe['empates'], 1)
            self.assertEqual(equipe['saldo_gols'], 0)

    def test_correcao_resultado(self):
        partida = self.criar_partida(
            status='realizada',
            gols_mandante=3,
            gols_visitante=1
        )

        tabela = calcular_classificacao(self.campeonato)

        self.assertEqual(tabela[0]['equipe'], self.equipe1)

        partida.gols_mandante = 1
        partida.gols_visitante = 4
        partida.save()

        tabela = calcular_classificacao(self.campeonato)

        self.assertEqual(tabela[0]['equipe'], self.equipe2)
        self.assertEqual(tabela[0]['pontos'], 3)

    def test_ignorar_partidas_nao_realizadas(self):
        self.criar_partida(status='agendada')
        self.criar_partida(status='adiada')
        self.criar_partida(status='cancelada')

        tabela = calcular_classificacao(self.campeonato)

        for equipe in tabela:
            self.assertEqual(equipe['jogos'], 0)
            self.assertEqual(equipe['pontos'], 0)

    def test_desempate_saldo_gols(self):
        equipe3 = Equipe.objects.create(
            nome='Bomba',
            cidade=self.cidade
        )

        inscricao3 = InscricaoEquipe.objects.create(
            equipe=equipe3,
            campeonato=self.campeonato,
            status='aprovada'
        )

        self.criar_partida(
            status='realizada',
            gols_mandante=3,
            gols_visitante=1
        )

        self.criar_partida(
            equipe_mandante=inscricao3,
            status='realizada',
            gols_mandante=1,
            gols_visitante=0
        )

        tabela = calcular_classificacao(self.campeonato)

        self.assertEqual(tabela[0]['equipe'], self.equipe1)
        self.assertEqual(tabela[1]['equipe'], equipe3)

    def test_separacao_partidas(self):
        self.criar_partida(
            status='realizada',
            gols_mandante=2,
            gols_visitante=1
        )

        self.criar_partida(
            horario=time(20, 0)
        )

        self.criar_partida(
            horario=time(10, 0)
        )

        self.criar_partida(status='adiada')
        self.criar_partida(status='cancelada')

        agora = timezone.make_aware(
            datetime(2026, 6, 10, 12, 0)
        )

        with patch(
            'campeonatos.services.timezone.localtime',
            return_value=agora
        ):
            partidas = separar_partidas(self.campeonato)

            self.assertEqual(partidas['realizadas'].count(), 1)
            self.assertEqual(partidas['proximas'].count(), 1)
            self.assertEqual(partidas['pendentes'].count(), 1)
            self.assertEqual(partidas['adiadas'].count(), 1)
            self.assertEqual(partidas['canceladas'].count(), 1)