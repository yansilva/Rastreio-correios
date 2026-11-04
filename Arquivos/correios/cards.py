"""Montagem do HTML dos cartões de pedido do painel (usada pelo relatório real e pela demonstração)."""
import unicodedata
from datetime import datetime
from html import escape

# Ordem em que os pedidos aparecem: o que pede ação do operador vem primeiro e os casos encerrados vão ao fim
# Dias com só a etiqueta nos Correios antes de avisar que o pedido "enviado" no Tiny não foi postado
DIAS_SEM_POSTAGEM = 2

PRIORIDADE_STATUS = {
    "aguardando_retirada": 0,
    "atrasado": 1,
    "sem_postagem": 2,
    "em_transito": 3,
    "nao_enviado": 4,
    "devolvido": 5,
    "entregue": 6,
}

# Explicação curta de cada status em pt-BR: usada no title e na descrição acessível das pílulas e dos selos,
# e na legenda de Opções. Um só lugar, para o texto não divergir.
DESCRICAO_STATUS = {
    "em_transito": "Objeto postado, a caminho do destinatário.",
    "atrasado": "Mais de 3 dias em trânsito desde a postagem.",
    "aguardando_retirada": "Objeto na agência, esperando o destinatário.",
    "sem_postagem": "O Tiny diz enviado, mas os Correios só têm a etiqueta.",
    "nao_enviado": "Pedido ainda não foi postado.",
    "entregue": "Objeto entregue ao destinatário.",
    "devolvido": "Objeto voltou ao remetente.",
}


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar a situação do Tiny."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn")
    return sem_acento.lower().strip()


def divergencia_tiny(categoria: str, situacao_tiny: str) -> str:
    """Mensagem quando a situação do Tiny contradiz o status dos Correios ('' quando coerente)."""
    tiny = _normalizar(situacao_tiny)
    if not tiny:
        return ""
    if categoria == "entregue" and tiny != "entregue":
        return f"Entregue nos Correios, mas o Tiny mostra '{situacao_tiny}'"
    if categoria == "devolvido" and tiny in ("enviado", "entregue"):
        return f"Devolvido nos Correios, mas o Tiny mostra '{situacao_tiny}'"
    return ""


def sem_postagem(categoria: str, situacao_tiny: str, dias_etiqueta: int | None) -> bool:
    """O Tiny diz 'enviado', mas os Correios só têm a etiqueta há mais de DIAS_SEM_POSTAGEM dias."""
    if categoria != "nao_enviado" or dias_etiqueta is None:
        return False
    tiny = _normalizar(situacao_tiny)
    return tiny in ("enviado", "postado", "em transito") and dias_etiqueta > DIAS_SEM_POSTAGEM


def esta_encerrado(categoria: str, *, retirada: bool = False, atrasado: bool = False) -> bool:
    """Casos já resolvidos: entregues e devolvidos, sem pendência de retirada ou atraso."""
    return categoria in ("entregue", "devolvido") and not retirada and not atrasado


def status_tokens(categoria: str, *, retirada: bool = False, atrasado: bool = False) -> str:
    """Valor de `data-status`: a categoria principal mais as derivadas usadas pelos filtros."""
    tokens = [categoria]
    if retirada and categoria not in ("entregue", "devolvido"):
        tokens.append("aguardando_retirada")
    if atrasado:
        tokens.append("atrasado")
    return " ".join(tokens)


def prioridade(categoria: str, *, retirada: bool = False, atrasado: bool = False) -> int:
    """Posição do pedido na lista: menor aparece antes."""
    if categoria in ("entregue", "devolvido"):
        return PRIORIDADE_STATUS[categoria]
    if retirada:
        return PRIORIDADE_STATUS["aguardando_retirada"]
    if atrasado:
        return PRIORIDADE_STATUS["atrasado"]
    return PRIORIDADE_STATUS.get(categoria, PRIORIDADE_STATUS["nao_enviado"])


def selo_status(
    categoria: str, *, retirada: bool = False, atrasado: bool = False, dias_atraso: int = 0
) -> tuple[str, str]:
    """Texto e classe de badge do status atual do pedido, para o cabeçalho do cartão."""
    if categoria == "devolvido":
        return "Devolvido", "badge-purple"
    if categoria == "entregue":
        return "Entregue", "badge-green"
    if retirada:
        return "Aguardando retirada", "badge-yellow"
    if atrasado:
        return f"Atrasado · {dias_atraso} dias", "badge-red"
    if categoria == "em_transito":
        return "Em trânsito", "badge-blue"
    return "Não enviado", "badge-yellow"


def chave_selo(categoria: str, *, retirada: bool = False, atrasado: bool = False) -> str:
    """Chave de DESCRICAO_STATUS para o selo que selo_status devolve (mesma ordem de precedência)."""
    if categoria in ("devolvido", "entregue"):
        return categoria
    if retirada:
        return "aguardando_retirada"
    if atrasado:
        return "atrasado"
    if categoria == "em_transito":
        return "em_transito"
    return "nao_enviado"


def textos_descricao() -> dict[str, str]:
    """Textos escapados para o template, com chaves `texto_<status>` (ex.: texto_atrasado)."""
    return {f"texto_{chave}": escape(texto, quote=True) for chave, texto in DESCRICAO_STATUS.items()}


def bloco_descricoes_status() -> str:
    """Textos de DESCRICAO_STATUS escondidos visualmente, com id para aria-describedby das pílulas."""
    itens = "".join(
        f'<span id="desc-status-{chave}">{escape(texto)}</span>' for chave, texto in DESCRICAO_STATUS.items()
    )
    # aria-hidden tira o texto do fluxo de leitura; aria-describedby ainda o lê ao focar a pílula
    return f'<div class="sr-only" aria-hidden="true">{itens}</div>'


def dias_desde(dt_iso: str, agora: datetime | None = None) -> int | None:
    """Dias corridos desde uma data ISO (None quando a data não é válida)."""
    try:
        data = datetime.fromisoformat(dt_iso)
    except (TypeError, ValueError):
        return None
    return ((agora or datetime.now()).date() - data.date()).days


def texto_idade(dt_iso: str, agora: datetime | None = None) -> str:
    """Há quanto tempo ocorreu o último evento ('' quando a data não é válida)."""
    dias = dias_desde(dt_iso, agora)
    if dias is None:
        return ""
    if dias <= 0:
        return "Último evento hoje"
    if dias == 1:
        return "Último evento ontem"
    return f"Último evento há {dias} dias"


def zero(numero: int) -> str:
    """Classe CSS que apaga a ênfase de um contador zerado (zero não pede atenção)."""
    return " is-zero" if numero == 0 else ""


def faixa_acao(atrasados: int, retiradas: int) -> str:
    """Faixa 'Precisam de ação': botões de filtro, ou uma linha calma quando não há nada a fazer."""
    if atrasados == 0 and retiradas == 0:
        return (
            '<section class="action-strip action-strip-ok" aria-label="Pedidos que precisam de ação">'
            '<svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg>'
            "<span>Nada atrasado nem aguardando retirada</span></section>"
        )

    def chip(filtro: str, icone: str, titulo: str, numero: int, rotulo: str) -> str:
        return (
            f'<button type="button" class="action-chip{zero(numero)}" data-filter="{filtro}" title="{titulo}">'
            f'<svg class="icon icon-{icone}" aria-hidden="true" focusable="false"><use href="#i-{icone}"></use></svg>'
            f"<strong>{numero}</strong> {rotulo}</button>"
        )

    return (
        '<section class="action-strip" aria-label="Pedidos que precisam de ação">'
        '<span class="action-strip-title">Precisam de ação</span>'
        + chip("atrasado", "clock", DESCRICAO_STATUS["atrasado"], atrasados, "Atrasados")
        + chip("aguardando_retirada", "building", DESCRICAO_STATUS["aguardando_retirada"], retiradas, "Aguardando retirada")
        + "</section>"
    )


def montar_card_pedido(
    *,
    titulo: str = "",
    tokens: str,
    selo: str,
    classe_selo: str,
    situacao_tiny: str,
    eventos_html: list[str],
    idade: str = "",
    oculto: bool = False,
    encerrado: bool = False,
    numero: str = "",
    idade_dias: int | None = None,
    divergencia: str = "",
    rastreio: str = "",
    cliente: str = "",
    numero_txt: str = "",
    chave_descricao: str = "",
) -> str:
    """Cartão de pedido: cabeçalho com status atual, último evento visível e histórico recolhido.

    Com numero_txt, o título sai em partes (número, cliente e código), cada uma num span; sem ele,
    o parâmetro titulo é usado como veio, para quem ainda o passa pronto.
    """
    classe = "order-card"
    if encerrado:
        classe += " order-closed"
    if oculto:
        classe += " order-hidden"
    idade_html = f'<span class="order-age">{escape(idade)}</span>' if idade else ""
    # Explicação do selo: title para o mouse e aria-describedby (texto escondido do bloco da página).
    # Fica fora do texto do selo, porque o painel copia o texto do selo para a tabela e para a busca.
    descricao_selo_attr = (
        f' title="{escape(DESCRICAO_STATUS[chave_descricao], quote=True)}" aria-describedby="desc-status-{chave_descricao}"'
        if chave_descricao
        else ""
    )
    divergencia_html = (
        f'<span class="badge badge-yellow" title="{escape(divergencia, quote=True)}">Tiny desatualizado</span>'
        if divergencia
        else ""
    )
    copiar_html = (
        f'<button type="button" class="btn-copy" data-copy="{escape(rastreio, quote=True)}" '
        f'aria-label="Copiar código de rastreio {escape(rastreio, quote=True)}">Copiar rastreio</button>'
        if rastreio
        else ""
    )
    if numero_txt:
        partes_titulo = [f'<span class="order-num">Pedido Tiny #{escape(numero_txt)}</span>']
        if cliente:
            partes_titulo.append(f'<span class="order-client">{escape(cliente)}</span>')
        if rastreio:
            partes_titulo.append(f'<span class="order-code">{escape(rastreio)}</span>')
        titulo_html = "".join(partes_titulo)
    else:
        titulo_html = escape(titulo)
    atributos = f'data-status="{tokens}"'
    if rastreio:
        atributos += f' data-rastreio="{escape(rastreio, quote=True)}"'
    if cliente:
        atributos += f' data-cliente="{escape(cliente, quote=True)}"'
    if numero:
        atributos += f' data-pedido="{escape(numero, quote=True)}"'
    if idade_dias is not None:
        atributos += f' data-idade="{idade_dias}"'

    historico = ""
    if len(eventos_html) > 1:
        rotulo = f"Ver histórico completo ({len(eventos_html)} eventos)"
        historico = (
            f'<details class="order-history"><summary>{rotulo}</summary>'
            f'{"".join(eventos_html[1:])}</details>'
        )

    return f"""
            <div class="{classe}" {atributos}>
                <div class="order-header">
                    <h2 class="order-title">{titulo_html}</h2>
                    <div class="order-meta">
                        <span class="badge {classe_selo}"{descricao_selo_attr}>{escape(selo)}</span>
                        {divergencia_html}
                        {idade_html}
                        <span class="order-tiny-status">Situação no Tiny: {escape(situacao_tiny or "—")}</span>
                        {copiar_html}
                    </div>
                </div>
                <div class="events-container">
                    {eventos_html[0] if eventos_html else ""}
                    {historico}
                </div>
            </div>
            """
