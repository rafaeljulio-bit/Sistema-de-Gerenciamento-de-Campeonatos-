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

    logo = models.ImageField(
        upload_to='campeonatos/',
        blank=True,
        null=True
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
            ('andamento', 'Em andamento'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        default='planejado'
    )

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()

        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError({
                    'data_fim': 'A data de término não pode ser anterior à data de início.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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

        if self.pk:
            anterior = JogadorEquipe.objects.get(pk=self.pk)
        
            if (
                 anterior.jogador_id != self.jogador_id
                or anterior.equipe_id != self.equipe_id
            ):
                if InscricaoJogador.objects.filter(
                    jogador_equipe=self
                ).exists():
                    raise ValidationError(
                        'Não é possível alterar um vínculo '
                        'com inscrições em campeonatos.'
                    )

        if self.data_saida and self.data_saida < self.data_entrada:
            raise ValidationError({ 'data_saida': 'A data de saída não pode ser anterior à data de entrada.' })
    class Meta:
        verbose_name = 'Vínculo de Jogador com equipe'
        verbose_name_plural = 'Vínculos de Jogadores com equipes'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
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
            ('cancelada', 'Cancelada'),
        ],
        default='pendente'
    )

    class Meta:
        verbose_name = 'Equipe inscrita em campeonato'
        verbose_name_plural = 'Equipes inscritas em campeonatos'

        constraints = [
            models.UniqueConstraint(
                fields=['equipe', 'campeonato'],
                name='unique_equipe_campeonato',
                violation_error_message='Esta equipe já está inscrita neste campeonato.'
            )
        ]

    def clean(self):
        super().clean()

        if self.pk:
            anterior = InscricaoEquipe.objects.get(pk=self.pk)

            if (
                anterior.equipe_id != self.equipe_id
                or anterior.campeonato_id != self.campeonato_id
            ):
                if(
                    self.jogadores_inscritos.exists()
                    or self.partidas_mandante.exists()
                    or self.partidas_visitante.exists()
                ):
                    raise ValidationError(
                        'Não é possível alterar a equipe ou o campeonato '
                        'de uma inscrição com registros vinculados.'
                    )

        if self.pk and self.status != 'aprovada':

            if self.jogadores_inscritos.exists():
                raise ValidationError(
                    'Esta equipe possui jogadores inscritos.'
                )

            if (
                self.partidas_mandante.exists()
                or self.partidas_visitante.exists()
            ):
                raise ValidationError(
                    'Esta equipe possui partidas vinculadas.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
        verbose_name = 'Jogador inscrito em campeonato'
        verbose_name_plural = 'Jogadores inscritos em campeonatos'

        constraints = [
            models.UniqueConstraint(
                fields=['jogador_equipe', 'inscricao_equipe'],
                name='vinculo_inscricao_unicos',
                violation_error_message='Este jogador já está inscrito nesta equipe para este campeonato.'
            )
        ]

    def clean(self):
        super().clean()

        if not self.jogador_equipe_id or not self.inscricao_equipe_id:
            return

        vinculo = self.jogador_equipe
        inscricao = self.inscricao_equipe
        campeonato = inscricao.campeonato

        if inscricao.status != 'aprovada':
            raise ValidationError(
                'A inscrição da equipe no campeonato não está aprovada'
            )

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
        
        InscricaoJogador.objects.filter(
            inscricao_equipe__campeonato=campeonato,
            jogador_equipe__jogador=vinculo.jogador
        ).exclude(pk=self.pk)

        if self.jogador_equipe_id and self.inscricao_equipe_id:

            inscricoes = InscricaoJogador.objects.filter(
                jogador_equipe__jogador=self.jogador_equipe.jogador,
                inscricao_equipe__campeonato=self.inscricao_equipe.campeonato
            ).exclude(pk=self.pk)

            if inscricoes.exclude(
                inscricao_equipe__equipe=self.inscricao_equipe.equipe
            ).exists():

                raise ValidationError(
                    'Este jogador já está inscrito em outra equipe neste campeonato.'
                )

            if inscricoes.filter(
                inscricao_equipe=self.inscricao_equipe
            ).exclude(
                jogador_equipe=self.jogador_equipe
            ).exists():

                raise ValidationError(
                    'Este jogador já está inscrito nesta equipe para este campeonato.'
                )

    def save(self, *args, **kwargs):
            self.full_clean()
            super().save(*args,**kwargs)

    def __str__(self):
            return (
                f'{self.jogador_equipe.jogador.nome} - '
                f'{self.inscricao_equipe.campeonato.nome}'
            )

class Partida(models.Model):

    STATUS_CHOICES =[
        ('agendada', 'Agendada'),
        ('adiada', 'Adiada'),
        ('cancelada', 'Cancelada'),
        ('realizada', 'Realizada'),
    ]

    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.PROTECT,
        related_name='partidas'
    )

    equipe_mandante = models.ForeignKey(
        InscricaoEquipe,
        on_delete=models.PROTECT,
        related_name='partidas_mandante'
    )

    equipe_visitante = models.ForeignKey(
        InscricaoEquipe,
        on_delete=models.PROTECT,
        related_name='partidas_visitante'
    )

    data = models.DateField()
    horario = models.TimeField()
    local = models.CharField(max_length=150)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='agendada'
    )


    gols_mandante = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    gols_visitante = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'campeonato',
                    'equipe_mandante',
                    'equipe_visitante',
                    'data',
                    'horario',
                ],
                name='unique_partida_campeonato',
                violation_error_message='Esta partida já está cadastrada neste campeonato.'
            )
        ]

    def clean(self):
        super().clean()

        if not self.campeonato_id:
            return

        if not self.equipe_mandante_id or not self.equipe_visitante_id:
            return

        mandante = self.equipe_mandante
        visitante = self.equipe_visitante

        if mandante.equipe_id == visitante.equipe_id:
            raise ValidationError(
                'Uma equipe não pode jogar contra ela mesma.'
            )

        if mandante.campeonato_id != self.campeonato_id:
            raise ValidationError(
                'A equipe mandante não pertence a este campeonato.'
            )

        if visitante.campeonato_id != self.campeonato_id:
            raise ValidationError(
                'A equipe visitante não pertence a este campeonato.'
            )

        if mandante.status != 'aprovada':
            raise ValidationError(
                'A inscrição da equipe mandante não está aprovada.'
            )

        if visitante.status != 'aprovada':
            raise ValidationError(
                'A inscrição da equipe visitante não está aprovada.'
            )

        if self.data:
            if self.data < self.campeonato.data_inicio:
                raise ValidationError(
                    'A partida não pode ocorrer antes do campeonato.'
                )

        if self.data:
            if self.data > self.campeonato.data_fim:
                raise ValidationError(
                    'A partida não pode ocorrer após o campeonato.'
                )

        if self.status == 'realizada':
            if self.gols_mandante is None or self.gols_visitante is None:
                raise ValidationError(
                    'Uma partida realizada deve possuir um placar.'
                )

        else:
            if self.gols_mandante is not None or self.gols_visitante is not None:
                raise ValidationError(
                    'Somente partidas realizadas podem possuir placar.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def resultado(self):

        if self.status != 'realizada':
            return None

        if self.gols_mandante is None or self.gols_visitante is None:
            return None

        if self.gols_mandante > self.gols_visitante:
            return 'mandante'

        elif self.gols_mandante < self.gols_visitante:
            return 'visitante'

        else:
            return 'empate'
        
    def __str__(self):
        return (
            f'{self.equipe_mandante.equipe} X '
            f'{self.equipe_visitante.equipe}'
        )