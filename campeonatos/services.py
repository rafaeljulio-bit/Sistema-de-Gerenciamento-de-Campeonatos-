from.models import InscricaoEquipe, Partida

def calcular_classificacao(campeonato):

    inscricoes = InscricaoEquipe.objects.filter(
        campeonato=campeonato,
        status='aprovada'
    ).select_related('equipe')

    classificacao = {}

    for inscricao in inscricoes:

        classificacao[inscricao.id] = {
            'equipe': inscricao.equipe,
            'pontos': 0,
            'jogos': 0,
            'vitorias': 0,
            'empates': 0,
            'derrotas': 0,
            'gols_pro': 0,
            'gols_contra': 0,
            'saldo_gols': 0,
        }

    partidas = Partida.objects.filter(
        campeonato=campeonato,
        status='realizada',
        gols_mandante__isnull=False,
        gols_visitante__isnull=False
    )

    for partida in partidas:

        mandante = classificacao.get(
            partida.equipe_mandante_id
        )

        visitante = classificacao.get(
            partida.equipe_visitante_id
        )

        if mandante is None or visitante is None:
            continue

        #contabilizar jogos
        mandante['jogos'] += 1
        visitante['jogos'] += 1

        #contabilizar gols
        mandante['gols_pro'] += partida.gols_mandante
        mandante['gols_contra'] += partida.gols_visitante

        visitante['gols_pro'] += partida.gols_visitante
        visitante['gols_contra'] += partida.gols_mandante

        resultado = partida.resultado()

        if resultado == 'mandante':
            mandante['pontos'] += 3
            mandante['vitorias'] += 1
            visitante['derrotas'] += 1

        elif resultado == 'visitante':
            visitante['pontos'] += 3
            visitante['vitorias'] += 1
            mandante['derrotas'] += 1

        elif resultado == 'empate':
            mandante['pontos'] += 1
            visitante['pontos'] += 1

            mandante['empates'] += 1
            visitante['empates'] += 1

    for equipe in classificacao.values():
        equipe['saldo_gols'] = (
            equipe['gols_pro'] - equipe['gols_contra']
        )

    tabela = sorted(
        classificacao.values(),
        key=lambda equipe: (
            -equipe['pontos'],
            -equipe['vitorias'],
            -equipe['saldo_gols'],
            -equipe['gols_pro'],
            equipe['equipe'].nome.lower()
        )
    )

    for posicao, equipe in enumerate(tabela, start=1):
        equipe['posicao']= posicao

    return tabela
