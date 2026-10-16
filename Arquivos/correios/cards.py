"""Montagem do HTML dos cartões de pedido do painel (usada pelo relatório real e pela demonstração)."""
from datetime import datetime
from html import escape

# Ordem em que os pedidos aparecem: o que pede ação do operador vem primeiro
PRIORIDADE_STATUS = {
    "aguardando_retirada": 0,
    "atrasado": 1,
    "devolvido": 2,
    "em_transito": 3,
    "nao_enviado": 4,
    "entregue": 5,
}


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


def texto_idade(dt_iso: str, agora: datetime | None = None) -> str:
    """Há quanto tempo ocorreu o último evento ('' quando a data não é válida)."""
    try:
        data = datetime.fromisoformat(dt_iso)
    except (TypeError, ValueError):
        return ""
    dias = ((agora or datetime.now()).date() - data.date()).days
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
) -> str:
    """Cartão de pedido: cabeçalho com status atual, último evento visível e histórico recolhido."""
    classe = "order-card order-hidden" if oculto else "order-card"
    idade_html = f'<span class="order-age">{escape(idade)}</span>' if idade else ""

    historico = ""
    if len(eventos_html) > 1:
        rotulo = f"Ver histórico completo ({len(eventos_html)} eventos)"
        historico = (
            f'<details class="order-history"><summary>{rotulo}</summary>'
            f'{"".join(eventos_html[1:])}</details>'
        )

    return f"""
            <div class="{classe}" data-status="{tokens}">
                <div class="order-header">
                    <div class="order-title">{escape(titulo)}</div>
                    <div class="order-meta">
                        <span class="badge {classe_selo}">{escape(selo)}</span>
                        {idade_html}
                        <span class="order-tiny-status">Tiny: {escape(situacao_tiny or "—")}</span>
                    </div>
                </div>
                <div class="events-container">
                    {eventos_html[0] if eventos_html else ""}
                    {historico}
                </div>
            </div>
            """
