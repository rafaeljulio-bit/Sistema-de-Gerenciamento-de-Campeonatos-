from django.db import models
from django.core.exceptions import ValidationError

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

class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    idade_maxima = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.nome

class Campeonato(models.Model):
    nome = models.CharField(max_length=100)
    modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.PROTECT,
        related_name='campeonatos'
    )

    categoria = models.ForeignKey(
            Categoria,
            on_delete=models.PROTECT,
            related_name='campeonatos',
            null=True,
            blank=True
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

    def jogador_elegivel(self, jogador):
        idade_no_ano = (
            self.data_inicio.year
            - jogador.data_nascimento.year
    )

        if self.categoria is None:
            return False
        
        if self.categoria.idade_maxima is None:
            return True

        return idade_no_ano <= self.categoria.idade_maxima

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

class Jogador(models.Model):
    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    cpf = models.CharField(max_length=11, unique=True)


    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'
    def __str__(self):
        return self.nome

class JogadorEquipe(models.Model):
    jogador = models.ForeignKey(
        Jogador,
        on_delete=models.PROTECT,
        related_name='vinculos'
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.PROTECT,
        related_name='jogadores_vinculados'
    )

    data_entrada = models.DateField()
    data_saida = models.DateField(
        null = True,
        blank = True
    )

    numero_camisa = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    def clean(self):
        super().clean()

        if self.data_saida and self.data_saida < self.data_entrada:
            raise ValidationError({ 'data_saida': 'A data de saída não pode ser anterior à data de entrada.' })
    class Meta:
        verbose_name = 'Vínculo de Jogador com equipe'
        verbose_name_plural = 'Vínculos de Jogadores com equipes'
    def __str__(self):
        return f"{self.jogador.nome} - {self.equipe.nome}"


class InscricaoEquipe(models.Model):
    equipe = models.ForeignKey(
        Equipe,
        on_delete= models.PROTECT,
        related_name='inscricoes'
    )

    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.PROTECT,
        related_name='equipes_inscritas'
    )

    data_inscricao = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
             ('pendente', 'Pendente'),
            ('aprovada', 'Aprovada'),
            ('Cancelada', 'Cancelada'),
        ],
        default='pendente'
    )

    class Meta:
        verbose_name = 'Equipe inscrita em campeonato'
        verbose_name_plural = 'Equipes inscritas em campeonatos'

        constraints = [
            models.UniqueConstraint(
                fields=['equipe', 'campeonato'],
                name='equipe_campeonato_unicos'
            )
        ]

    def __str__(self):
            return f'{self.equipe.nome} - {self.campeonato.nome}'
        
class InscricaoJogador(models.Model):
    jogador_equipe = models.ForeignKey(
        JogadorEquipe,
        on_delete=models.PROTECT,
        related_name='inscricoes'
    )

    inscricao_equipe = models.ForeignKey(
        InscricaoEquipe,
        on_delete=models.PROTECT,
        related_name='jogadores_inscritos'
    )

    data_inscricao = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jogadore inscrito em campeonato'
        verbose_name_plural = 'Jogadores inscritos em campeonatos'

        constraints = [
            models.UniqueConstraint(
                fields=['jogador_equipe', 'inscricao_equipe'],
                name='vinculo_inscricao_unicos'
            )
        ]

    def clean(self):
        super().clean()

        if not self.jogador_equipe_id or not self.inscricao_equipe_id:
            return

        vinculo = self.jogador_equipe
        inscricao = self.inscricao_equipe
        campeonato = inscricao.campeonato

        if vinculo.equipe_id != inscricao.equipe_id:
            raise ValidationError(
                'O jogador não pertence à equipe inscrita.'
            )

        if vinculo.data_entrada > campeonato.data_inicio:
            raise ValidationError(
                'O jogador ainda não estava vinculado à equipe no início do campeonato.'
            )

        if (
            vinculo.data_saida is not None
            and vinculo.data_saida < campeonato.data_inicio
        ):
            raise ValidationError(
                'O jogador não estava mais vinculado à equipe no início do campeonato.'
            )
        
        if not campeonato.jogador_elegivel(vinculo.jogador):
            raise ValidationError('O jogador não é elegível para a categoria do campeonato.'
            )
        
        duplicado = InscricaoJogador.objects.filter(
            inscricao_equipe__campeonato=campeonato,
            jogador_equipe__jogador=vinculo.jogador
        ).exclude(pk=self.pk)

        if duplicado.exists():
            raise ValidationError(
                'Este jogador já está inscrito em outra equipe neste campeonato.'
        )

    def save(self, *args, **kwargs):
            self.full_clean()
            super().save(*args,**kwargs)

    def __str__(self):
            return (
                f'{self.jogador_equipe.jogador.nome} - '
                f'{self.inscricao_equipe.campeonato.nome}'
            )
