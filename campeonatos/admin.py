from django.contrib import admin
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
# Register your models here.
