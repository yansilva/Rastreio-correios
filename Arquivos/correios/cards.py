"""Montagem do HTML dos cartões de pedido do painel (usada pelo relatório real e pela demonstração)."""
import unicodedata
from datetime import datetime
from html import escape

# Ordem em que os pedidos aparecem: o que pede ação do operador vem primeiro e os casos encerrados vão ao fim
PRIORIDADE_STATUS = {
    "aguardando_retirada": 0,
    "atrasado": 1,
    "em_transito": 2,
    "nao_enviado": 3,
    "devolvido": 4,
    "entregue": 5,
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
        return "Aguardando retirada", "badge-red"
    if atrasado:
        return f"Atrasado · {dias_atraso} dias", "badge-red"
    if categoria == "em_transito":
        return "Em trânsito", "badge-blue"
    return "Não enviado", "badge-yellow"


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


def montar_card_pedido(
    *,
    titulo: str,
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
) -> str:
    """Cartão de pedido: cabeçalho com status atual, último evento visível e histórico recolhido."""
    classe = "order-card"
    if encerrado:
        classe += " order-closed"
    if oculto:
        classe += " order-hidden"
    idade_html = f'<span class="order-age">{escape(idade)}</span>' if idade else ""
    divergencia_html = (
        f'<span class="badge badge-yellow" title="{escape(divergencia, quote=True)}">Tiny desatualizado</span>'
        if divergencia
        else ""
    )
    atributos = f'data-status="{tokens}"'
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
                    <div class="order-title">{escape(titulo)}</div>
                    <div class="order-meta">
                        <span class="badge {classe_selo}">{escape(selo)}</span>
                        {divergencia_html}
                        {idade_html}
                        <span class="order-tiny-status">Situação no Tiny: {escape(situacao_tiny or "—")}</span>
                    </div>
                </div>
                <div class="events-container">
                    {eventos_html[0] if eventos_html else ""}
                    {historico}
                </div>
            </div>
            """
