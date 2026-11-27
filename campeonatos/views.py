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