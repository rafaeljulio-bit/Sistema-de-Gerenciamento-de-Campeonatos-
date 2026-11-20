from django.contrib import admin
from .models import (
Cidade, 
Modalidade,
Categoria, 
Campeonato, 
Equipe, 
Jogador,
)
admin.site.register(Cidade)
admin.site.register(Modalidade)
admin.site.register(Categoria)
admin.site.register(Campeonato)
admin.site.register(Equipe)
admin.site.register(Jogador)
# Register your models here.
