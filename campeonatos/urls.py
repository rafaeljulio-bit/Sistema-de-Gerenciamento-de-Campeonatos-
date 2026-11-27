from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [

    path('', views.home, name='home'),

    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        next_page='home'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),

    path('cadastro/', views.cadastro, name='cadastro'),

    path('perfil/', views.perfil, name='perfil'),

    path(
        'alterarSenha/',
        auth_views.PasswordChangeView.as_view(
            template_name='alterarSenha.html',
            success_url=reverse_lazy('perfil')
        ),
        name='alterarSenha'
    ),

    path('perfil/editar/', views.editarPerfil, name='editarPerfil'),
    path('painel/', views.painel, name='painel'),

        path(
        'gerenciamento/<str:tipo>/',
        views.listarCadastro,
        name='listarCadastro'
    ),

    path(
        'gerenciamento/<str:tipo>/adicionar/',
        views.adicionarCadastro,
        name='adicionarCadastro'
    ),

    path(
        'gerenciamento/<str:tipo>/<int:pk>/editar/',
        views.editarCadastro,
        name='editarCadastro'
    ),

    path(
        'gerenciamento/<str:tipo>/<int:pk>/excluir/',
        views.excluirCadastro,
        name='excluirCadastro'
    ),

    path(
    'classificacao/',
    views.classificacaoPublica,
    name='classificacaoPublica'
    ),

    path(
    'campeonatos/',
    views.listarCampeonatos,
    name='listarCampeonatos'
),

path(
    'campeonatos/<int:pk>/',
    views.detalhesCampeonato,
    name='detalhesCampeonato'
),

path(
    'partidas/',
    views.partidasPublicas,
    name='partidasPublicas'
),

path(
    'usuarios/',
    views.listarUsuarios,
    name='listarUsuarios'
),

path(
    'usuarios/adicionar/',
    views.adicionarUsuario,
    name='adicionarUsuario'
),

path(
    'usuarios/<int:pk>/editar/',
    views.editarUsuario,
    name='editarUsuario'
),
]