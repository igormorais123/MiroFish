from app.services.strategic_density_gate import StrategicDensityGate


def test_generic_report_fails_density_gate():
    report = """
    O melhor caminho e agir com prudencia, manter comunicacao clara e buscar estabilidade.
    E importante organizar documentos e evitar conflitos.
    """
    result = StrategicDensityGate().evaluate(report)
    assert result["passes_gate"] is False
    assert result["non_generic_score"] < 0.70
    assert "tese_adversaria_ausente" in result["issues"]


def test_actionable_adversarial_report_passes_density_gate():
    report = """
    Tese vencedora: modular o pedido como reducao de risco, nao como confronto.
    Tese adversaria mais forte: a autora dira que os embargos rediscutem merito.
    Cortar da peca: qualquer frase que sugira descumprimento ou ataque ao juizo.
    Pedido seguro agora: calendario operacional e transicao gradual.
    Pedido perigoso agora: nulidade total como primeiro pedido liminar.
    Matriz 15/30/60: em 15 dias consolidar comprovantes; em 30 dias memorial; em 60 dias avaliar estudo.
    Documentos indispensaveis: IDs 257716387, 271866597, 272902574, 272931330 e 274563093.
    Perguntas provaveis do decisor: por que a rotina anterior protege melhor a crianca?
    Gatilhos de reversao: novo incidente reiterado, laudo tecnico forte ou descumprimento documentado.
    Ganho sobre o obvio: o pedido principal deve ser modulado, e a nulidade deve operar como fundamento.
    """
    result = StrategicDensityGate().evaluate(report)
    assert result["passes_gate"] is True
    assert result["decision_delta_score"] >= 0.85


def test_keyword_only_report_fails_density_gate():
    report = (
        "Tese vencedora. Tese adversaria. Cortar. Pedido seguro. Pedido perigoso. "
        "Matriz 15/30/60. Documentos. Decisor. Gatilhos de reversao. Ganho sobre o obvio."
    )

    result = StrategicDensityGate().evaluate(report)

    assert result["passes_gate"] is False
    assert result["substantive_score"] < 0.65
    assert "conteudo_substantivo_insuficiente" in result["issues"]


def test_actionable_report_with_alternative_vocabulary_passes_density_gate():
    report = """
    Estrategia recomendada: a posicao principal e uma proposta principal de ajuste operacional.
    Objecao: a outra parte dira que a medida tenta rediscutir fatos ja decididos.
    Risco de leitura: o decisor pode entender que ha tentativa de punicao indireta.
    Excluir da minuta o ataque pessoal; nao usar adjetivos, remover excessos e suprimir repeticoes.
    Providencia imediata: adotar medida prudente com pedido seguro nos proximos dias.
    Pedido perigoso: ha risco de parecer precipitado se pedir reversao integral agora.
    15/30/60: 15 dias para anexos; 30 dias para comprovantes; 60 dias para revisar a rota.
    Documentos indispensaveis: provas, evidencias, IDs 257716387 e comprovantes de cumprimento.
    Perguntas provaveis: juiz pode perguntar qual fato novo existe; ponto que sera cobrado.
    Gatilhos de reversao: se surgir prova nova ou se ocorrer descumprimento, mudaria a conclusao.
    Ganho sobre o obvio: a decisao superior esta no diferencial; nao e apenas repetir o pedido.
    """

    result = StrategicDensityGate().evaluate(report)

    assert result["passes_gate"] is True
    assert result["final_score"] >= 0.70


def test_generic_family_report_with_strategy_labels_fails_density_gate():
    report = """
    Linha recomendada: agir com prudencia, manter comunicacao clara e buscar estabilidade.
    Tese adversaria: a outra parte pode discordar e tentar mostrar que Igor nao cooperou.
    Cortar excessos e evitar conflitos para que o processo fique mais objetivo.
    Pedido seguro agora: organizar documentos e pedir uma solucao equilibrada.
    Pedido perigoso agora: qualquer medida que pareca exagerada.
    Matriz 15/30/60: em 15 dias revisar mensagens, em 30 dias organizar documentos e em 60 dias avaliar proximos passos.
    Perguntas provaveis do decisor: se Igor esta agindo de boa-fe.
    Gatilhos de reversao: qualquer fato novo relevante.
    Ganho sobre o obvio: o relatorio indica cautela e foco na crianca.
    """

    result = StrategicDensityGate().evaluate(report)

    assert result["passes_gate"] is False
    assert result["case_specific_score"] < 0.70
    assert "densidade_caso_familiar_insuficiente" in result["issues"]


def test_real_family_legal_strategy_report_passes_density_gate():
    report = """
    Linha recomendada: cumprir impecavelmente a rotina atual, pedir calendario operacional claro
    e produzir dossie de estabilidade; a ampliacao de convivio deve aparecer como consequencia
    possivel da previsibilidade comprovada, nao como pedido maximalista inicial. A medida segura
    agora e defender pericia ou estudo psicossocial bilateral para retirar escola e saude do
    terreno de disputa pessoal.

    Tese adversaria mais forte: a parte contraria dira que falas de Igor mostram pressao,
    que o excesso de mensagens cria instabilidade e que atraso ou ambiguidade de calendario
    prova falta de cooperacao. O MP ou juiz pode interpretar discussao medica, medicacao ou
    novo conflito na escola como sinal de que o conflito parental contaminou a rotina da crianca.

    Cortar da peca: ataque pessoal, disputa sobre quem tem razao na escola, julgamento leigo
    sobre saude/medicacao e qualquer frase que pareca retaliacao. Nao pedir agora ampliacao
    brusca ou reversao integral como primeiro pedido, porque isso parece precipitado.

    Pedidos seguros agora: calendario operacional objetivo, canal unico de comunicacao,
    comprovacao de cumprimento, dossie de estabilidade e estudo psicossocial bilateral.
    Pedidos precipitados ou perigosos agora: ampliar convivencia como exigencia maximalista,
    discutir medicacao como disputa pessoal ou imputar culpa escolar sem documento tecnico.

    Documentos 15/30/60: em 15 dias reunir comprovantes de cumprimento, mensagens essenciais
    e ocorrencias escolares objetivas; em 30 dias fechar linha do tempo com recibos, agenda,
    comunicados da escola e registros de saude; em 60 dias consolidar relatorio profissional,
    laudo ou estudo psicossocial e comparar estabilidade antes de pedir ampliacao.

    Perguntas provaveis do decisor: o que muda em relacao ao obvio, qual pedido reduz conflito
    hoje e qual documento prova estabilidade sem transformar escola e saude em disputa pessoal.
    Gatilhos de reversao: atraso repetido, recusa documentada de calendario, laudo tecnico,
    orientacao profissional sobre medicacao ou novo conflito escolar confirmado.
    Ganho sobre o obvio: a decisao muda porque o foco sai de vencer a mae e passa a demonstrar
    previsibilidade verificavel; isso cria base para ampliacao como consequencia, nao como salto.
    """

    result = StrategicDensityGate().evaluate(report)

    assert result["passes_gate"] is True
    assert result["case_specific_score"] >= 0.85


def test_density_gate_returns_clear_portuguese_issue_labels():
    result = StrategicDensityGate().evaluate("Relatorio generico com comunicacao clara.")

    assert result["hits"]["issues"]["tese_adversaria_ausente"] == "Falta a tese adversaria mais forte."
    assert result["hits"]["issues"]["decisao_sem_delta"] == "Nao explica qual decisao muda em relacao ao obvio."
