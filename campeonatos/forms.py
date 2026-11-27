from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Cidade, Modalidade, Categoria
from .models import Campeonato, Equipe, Jogador
from .models import JogadorEquipe, InscricaoEquipe, InscricaoJogador
from .models import Partida
from .models import EstatisticaPartida

class CadastroVisitanteForm(UserCreationForm):

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )


class PerfilForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )

class CidadeForm(forms.ModelForm):

    class Meta:
        model = Cidade
        fields = ['nome', 'uf']


class ModalidadeForm(forms.ModelForm):

    class Meta:
        model = Modalidade
        fields = ['nome', 'descricao']


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ['nome', 'idade_maxima']

class CampeonatoForm(forms.ModelForm):

    class Meta:
        model = Campeonato
        fields = [
            'nome',
            'modalidade',
            'categoria',
            'cidade',
            'descricao',
            'data_inicio',
            'data_fim',
            'status',
            'logo',
        ]

        widgets = {
            'data_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'data_fim': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }


class EquipeForm(forms.ModelForm):

    class Meta:
        model = Equipe
        fields = [
            'nome',
            'cidade',
            'escudo',
        ]


class JogadorForm(forms.ModelForm):

    class Meta:
        model = Jogador
        fields = [
            'nome',
            'data_nascimento',
            'cpf',
        ]

        widgets = {
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }

class JogadorEquipeForm(forms.ModelForm):

    class Meta:
        model = JogadorEquipe
        fields = [
            'jogador',
            'equipe',
            'data_entrada',
            'data_saida',
            'numero_camisa',
        ]

        widgets = {
            'data_entrada': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'data_saida': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }


class InscricaoEquipeForm(forms.ModelForm):

    class Meta:
        model = InscricaoEquipe
        fields = [
            'equipe',
            'campeonato',
            'status',
        ]


class InscricaoJogadorForm(forms.ModelForm):

    class Meta:
        model = InscricaoJogador
        fields = [
            'jogador_equipe',
            'inscricao_equipe',
        ]

class PartidaForm(forms.ModelForm):

    class Meta:
        model = Partida
        fields = [
            'campeonato',
            'equipe_mandante',
            'equipe_visitante',
            'data',
            'horario',
            'local',
            'status',
            'gols_mandante',
            'gols_visitante',
        ]

        widgets = {
            'data': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'horario': forms.TimeInput(
                format='%H:%M',
                attrs={'type': 'time'}
            ),
        }

class CadastroOrganizadorForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]

    def __init__(self, *args, permitirAdministrador=False, **kwargs):

        super().__init__(*args, **kwargs)

        if permitirAdministrador:

            self.fields['tipoConta'] = forms.ChoiceField(
                label='Tipo de conta',
                choices=[
                    ('Organizador', 'Organizador'),
                    ('Administrador', 'Administrador'),
                ]
            )


class EditarOrganizadorForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
        ]

class SelecaoEstatistica(forms.Select):

    def create_option(
        self, name, value, label, selected,
        index, subindex=None, attrs=None
    ):

        opcao = super().create_option(
            name, value, label, selected,
            index, subindex, attrs
        )

        instancia = getattr(value, 'instance', None)

        if isinstance(instancia, Partida):

            opcao['attrs']['data-mandante'] = (
                instancia.equipe_mandante_id
            )

            opcao['attrs']['data-visitante'] = (
                instancia.equipe_visitante_id
            )

        elif isinstance(instancia, InscricaoJogador):

            opcao['attrs']['data-equipe'] = (
                instancia.inscricao_equipe_id
            )

        return opcao

class EstatisticaPartidaForm(forms.ModelForm):

    class Meta:
        model = EstatisticaPartida

        fields = [
            'partida',
            'inscricao_jogador',
            'gols',
            'assistencias',
        ]

        labels = {
            'partida': 'Partida',
            'inscricao_jogador': 'Jogador inscrito',
            'gols': 'Gols',
            'assistencias': 'Assistências',
        }

        widgets = {
            'partida': SelecaoEstatistica(),
            'inscricao_jogador': SelecaoEstatistica(),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['partida'].queryset = (
            Partida.objects.filter(status='realizada')
            .select_related(
                'equipe_mandante__equipe',
                'equipe_visitante__equipe',
                'campeonato'
            ).order_by('id')
        )

        self.fields['partida'].label_from_instance = (
            lambda partida:
            f'{partida.equipe_mandante.equipe.nome} '
            f'{partida.gols_mandante} x '
            f'{partida.gols_visitante} '
            f'{partida.equipe_visitante.equipe.nome} | '
            f'{partida.campeonato.nome} | '
            f'{partida.data:%d/%m/%Y}'
        )

        self.fields['inscricao_jogador'].queryset = (
            InscricaoJogador.objects.select_related(
                'jogador_equipe__jogador',
                'inscricao_equipe__equipe',
                'inscricao_equipe__campeonato'
            ).order_by('id')
        )

        self.fields['inscricao_jogador'].label_from_instance = (
            lambda inscricao:
            f'{inscricao.jogador_equipe.jogador.nome} | '
            f'{inscricao.inscricao_equipe.equipe.nome} | '
            f'{inscricao.inscricao_equipe.campeonato.nome}'
        )