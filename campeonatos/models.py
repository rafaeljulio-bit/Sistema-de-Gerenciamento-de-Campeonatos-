from django.db import models

class Modalidade(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome

class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'uf'],
                name='cidade_nome_uf_unicos'
            )
        ]
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.uf}"

class Campeonato(models.Model):
    nome = models.CharField(max_length=100)
    modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.PROTECT,
        related_name='campeonatos'
    )
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name='campeonatos',
        null=True,
        blank=True
    )
    descricao = models.TextField(blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('planejado', 'planejado'),
            ('andamento', 'andamento'),
        ],
        default='planejado'
    )

    def __str__(self):
        return self.nome

class Equipe(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name='equipes',
        null=True,
        blank=True
    )
    escudo = models.ImageField(
        upload_to='escudos/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nome

# Create your models here.
