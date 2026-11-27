from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import CadastroVisitanteForm, PerfilForm
from django.core.exceptions import PermissionDenied
from .models import Campeonato, Equipe, Jogador, Partida
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models.deletion import ProtectedError
from .models import Cidade, Modalidade, Categoria
from .forms import CidadeForm, ModalidadeForm, CategoriaForm
from .forms import CampeonatoForm, EquipeForm, JogadorForm
from .models import JogadorEquipe, InscricaoEquipe, InscricaoJogador
from .forms import PartidaForm
from .services import calcular_classificacao
from .services import separar_partidas
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .forms import (
    CadastroOrganizadorForm,
    EditarOrganizadorForm,
)
from .forms import (
    JogadorEquipeForm,
    InscricaoEquipeForm,
    InscricaoJogadorForm,
)

def home(request):
    return render(request, 'index.html')


def cadastro(request):

    if request.user.is_authenticated:
        return redirect('perfil')

    if request.method == 'POST':

        form = CadastroVisitanteForm(request.POST)

        if form.is_valid():

            with transaction.atomic():
                usuario = form.save(commit=False)

                usuario.is_staff = False
                usuario.is_superuser = False

                usuario.save()

                grupo = Group.objects.get(name='Visitante')
                usuario.groups.add(grupo)

            return redirect('login')

    else:
        form = CadastroVisitanteForm()

    return render(request, 'cadastro.html', {
        'form': form
    })


@login_required(login_url='login')
def perfil(request):
    return render(request, 'perfil.html')


@login_required(login_url='login')
def editarPerfil(request):

    if request.method == 'POST':

        form = PerfilForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Perfil atualizado com sucesso!'
            )

            return redirect('perfil')

    else:
        form = PerfilForm(instance=request.user)

    return render(request, 'editarPerfil.html', {
        'form': form
    })

@login_required(login_url='login')
def painel(request):

    if not request.user.is_staff:
        raise PermissionDenied

    if not request.user.is_superuser:
        if not request.user.groups.filter(
            name__in=['Administrador', 'Organizador']
        ).exists():
            raise PermissionDenied

    contexto = {
        'totalCampeonatos': Campeonato.objects.count(),
        'totalEquipes': Equipe.objects.count(),
        'totalJogadores': Jogador.objects.count(),
        'totalPartidas': Partida.objects.count(),
        'gerenciarUsuarios': request.user.has_perm('auth.add_user'),
    }

    return render(request, 'painel.html', contexto)

CADASTROS = {
    'cidades': {
        'modelo': Cidade,
        'form': CidadeForm,
        'titulo': 'Cidades',
    },

    'modalidades': {
        'modelo': Modalidade,
        'form': ModalidadeForm,
        'titulo': 'Modalidades',
    },

    'categorias': {
        'modelo': Categoria,
        'form': CategoriaForm,
        'titulo': 'Categorias',
    },

        'campeonatos': {
        'modelo': Campeonato,
        'form': CampeonatoForm,
        'titulo': 'Campeonatos',
    },

    'equipes': {
        'modelo': Equipe,
        'form': EquipeForm,
        'titulo': 'Equipes',
    },

    'jogadores': {
        'modelo': Jogador,
        'form': JogadorForm,
        'titulo': 'Jogadores',
    },

        'vinculosJogadores': {
        'modelo': JogadorEquipe,
        'form': JogadorEquipeForm,
        'titulo': 'Vínculos de jogadores',
    },

    'inscricoesEquipes': {
        'modelo': InscricaoEquipe,
        'form': InscricaoEquipeForm,
        'titulo': 'Inscrições de equipes',
    },

    'inscricoesJogadores': {
        'modelo': InscricaoJogador,
        'form': InscricaoJogadorForm,
        'titulo': 'Inscrições de jogadores',
    },

        'partidas': {
        'modelo': Partida,
        'form': PartidaForm,
        'titulo': 'Partidas e resultados',
    },
}


def verificarPermissao(request, tipo, acao):

    if tipo not in CADASTROS:
        raise Http404

    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied

    if not request.user.is_superuser:
        if not request.user.groups.filter(
            name__in=['Administrador', 'Organizador']
        ).exists():
            raise PermissionDenied

    cadastro = CADASTROS[tipo]

    modelo = cadastro['modelo']

    permissao = (
        f'campeonatos.{acao}_{modelo._meta.model_name}'
    )

    if not request.user.has_perm(permissao):
        raise PermissionDenied

    return cadastro


@login_required(login_url='login')
def listarCadastro(request, tipo):

    cadastro = verificarPermissao(request, tipo, 'view')

    registros = cadastro['modelo'].objects.all().order_by('id')

    return render(request, 'listarCadastro.html', {
        'registros': registros,
        'titulo': cadastro['titulo'],
        'tipo': tipo,
    })


@login_required(login_url='login')
def adicionarCadastro(request, tipo):

    cadastro = verificarPermissao(request, tipo, 'add')

    if request.method == 'POST':

        form = cadastro['form'](
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Cadastro realizado com sucesso!'
            )

            return redirect('listarCadastro', tipo=tipo)

    else:
        form = cadastro['form']()

    return render(request, 'formCadastro.html', {
        'form': form,
        'titulo': 'Adicionar - ' + cadastro['titulo'],
        'tipo': tipo,
    })


@login_required(login_url='login')
def editarCadastro(request, tipo, pk):

    cadastro = verificarPermissao(request, tipo, 'change')

    registro = get_object_or_404(
        cadastro['modelo'],
        pk=pk
    )

    if request.method == 'POST':

        form = cadastro['form'](
            request.POST,
            request.FILES,
            instance=registro
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Cadastro atualizado com sucesso!'
            )

            return redirect('listarCadastro', tipo=tipo)

    else:
        form = cadastro['form'](instance=registro)

    return render(request, 'formCadastro.html', {
        'form': form,
        'titulo': 'Editar - ' + cadastro['titulo'],
        'tipo': tipo,
    })


@login_required(login_url='login')
def excluirCadastro(request, tipo, pk):

    cadastro = verificarPermissao(request, tipo, 'delete')

    registro = get_object_or_404(
        cadastro['modelo'],
        pk=pk
    )

    if request.method == 'POST':

        try:
            registro.delete()

            messages.success(
                request,
                'Registro excluído com sucesso!'
            )

        except ProtectedError:

            messages.error(
                request,
                'Não é possível excluir um registro '
                'que possui outros cadastros vinculados.'
            )

        return redirect('listarCadastro', tipo=tipo)

    return render(request, 'excluirCadastro.html', {
        'registro': registro,
        'tipo': tipo,
    })

def classificacaoPublica(request):

    campeonatos = Campeonato.objects.all().order_by('id')

    campeonato = None
    classificacao = []

    campeonatoId = request.GET.get('campeonato')

    if campeonatoId:

        if not campeonatoId.isdecimal():
            raise Http404

        campeonato = get_object_or_404(
            campeonatos,
            pk=campeonatoId
        )

        classificacao = calcular_classificacao(campeonato)

    return render(request, 'classificacaoPublica.html', {
        'campeonatos': campeonatos,
        'campeonato': campeonato,
        'classificacao': classificacao,
    })

def listarCampeonatos(request):

    campeonatos = Campeonato.objects.all().order_by('id')

    return render(request, 'listarCampeonatos.html', {
        'campeonatos': campeonatos,
    })


def detalhesCampeonato(request, pk):

    campeonato = get_object_or_404(Campeonato, pk=pk)

    equipes = InscricaoEquipe.objects.filter(
        campeonato=campeonato,
        status='aprovada'
    ).select_related('equipe').order_by('id')

    return render(request, 'detalhesCampeonato.html', {
        'campeonato': campeonato,
        'equipes': equipes,
        'totalEquipes': equipes.count(),
    })  

def partidasPublicas(request):

    campeonatos = Campeonato.objects.all().order_by('id')

    campeonato = None
    partidas = []

    campeonatoId = request.GET.get('campeonato')
    situacao = request.GET.get('situacao', 'proximas')

    situacoes = {
        'proximas': 'Próximas partidas',
        'realizadas': 'Resultados anteriores',
        'pendentes': 'Partidas pendentes',
        'adiadas': 'Partidas adiadas',
        'canceladas': 'Partidas canceladas',
    }

    if situacao not in situacoes:
        situacao = 'proximas'

    if campeonatoId:

        if not campeonatoId.isdecimal():
            raise Http404

        campeonato = get_object_or_404(
            campeonatos,
            pk=campeonatoId
        )

        partidas = separar_partidas(campeonato)[situacao]

    return render(request, 'partidasPublicas.html', {
        'campeonatos': campeonatos,
        'campeonato': campeonato,
        'partidas': partidas,
        'situacao': situacao,
        'situacoes': situacoes,
        'tituloSituacao': situacoes[situacao],
    })

def verificarGerenciamentoUsuarios(request, acao):

    usuario = request.user

    if not usuario.is_active or not usuario.is_staff:
        raise PermissionDenied

    if not usuario.is_superuser:
        if not usuario.groups.filter(
            name='Administrador'
        ).exists():
            raise PermissionDenied

    if not usuario.has_perm(f'auth.{acao}_user'):
        raise PermissionDenied


def consultarOrganizadores():

    return User.objects.filter(
        groups__name='Organizador',
        is_staff=True,
        is_superuser=False,
        user_permissions__isnull=True
    ).exclude(
        groups__in=Group.objects.exclude(name='Organizador')
    ).distinct().order_by('id')


@login_required(login_url='login')
def listarUsuarios(request):

    verificarGerenciamentoUsuarios(request, 'view')

    usuarios = consultarUsuariosGerenciaveis(
        request.user
    ).prefetch_related('groups')

    for usuario in usuarios:

        usuario.tipoConta = ', '.join(
            grupo.name for grupo in usuario.groups.all()
        )

    return render(request, 'listarUsuarios.html', {
        'usuarios': usuarios,
    })


@login_required(login_url='login')
def adicionarUsuario(request):

    verificarGerenciamentoUsuarios(request, 'add')

    if request.method == 'POST':

        form = CadastroOrganizadorForm(
            request.POST,
            permitirAdministrador=request.user.is_superuser
        )

        if form.is_valid():

            with transaction.atomic():

                usuario = form.save(commit=False)
                usuario.is_staff = True
                usuario.is_superuser = False
                usuario.save()

                tipoConta = 'Organizador'

                if request.user.is_superuser:
                    tipoConta = form.cleaned_data['tipoConta']

                grupo = Group.objects.get(name=tipoConta)
                usuario.groups.add(grupo)

            messages.success(
                request,
                'Usuário cadastrado com sucesso!'
            )

            return redirect('listarUsuarios')

    else:

        form = CadastroOrganizadorForm(
            permitirAdministrador=request.user.is_superuser
        )

    return render(request, 'formUsuario.html', {
        'form': form,
        'titulo': 'Cadastrar usuário',
    })


@login_required(login_url='login')
def editarUsuario(request, pk):

    verificarGerenciamentoUsuarios(request, 'change')

    usuario = get_object_or_404(
        consultarUsuariosGerenciaveis(request.user),
        pk=pk
    )

    if request.method == 'POST':

        form = EditarOrganizadorForm(
            request.POST,
            instance=usuario
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Organizador atualizado com sucesso!'
            )

            return redirect('listarUsuarios')

    else:
        form = EditarOrganizadorForm(instance=usuario)

    return render(request, 'formUsuario.html', {
        'form': form,
        'titulo': 'Editar usuário',
    })

def consultarUsuariosGerenciaveis(usuario):

    organizadores = consultarOrganizadores()

    filtro = Q(pk__in=organizadores.values('pk'))

    if usuario.is_superuser:

        filtro |= Q(
            groups__name='Administrador',
            is_superuser=False
        )

    return User.objects.filter(
        filtro
    ).distinct().order_by('id')