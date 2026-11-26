from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import CadastroVisitanteForm, PerfilForm
from django.core.exceptions import PermissionDenied
from .models import Campeonato, Equipe, Jogador, Partida

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