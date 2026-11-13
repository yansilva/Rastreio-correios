"""Menu de abas (`<nav class="nav-tabs">`) das páginas do painel. Única fonte da ordem e dos rótulos.

Regra da contagem de atrasados: a aba "Atrasados" aparece em todas as páginas, na mesma posição.
O número ao lado do rótulo só aparece quando a página recebe a contagem e ela é maior que zero
(Zero Is Calm). Páginas que não recebem a contagem mostram a aba sem número.
"""

from correios.icons import icone

# Ordem única do menu: (chave, arquivo, rótulo, ícone)
ABAS = (
    ("painel", "relatorio_rastreio.html", "Painel", "bar-chart"),
    ("atrasados", "pedidos_atrasados.html", "Atrasados", "clock"),
    ("entregues", "entregues_semana.html", "Entregues", "check-circle"),
    ("frete", "opcoes_frete.html", "Opções de Frete", "package"),
)

CHAVES = tuple(chave for chave, *_ in ABAS)


def nav_html(ativa: str, atrasados: int | None = None) -> str:
    """Devolve o `<nav>` completo, com a aba `ativa` marcada como página atual.

    `atrasados` é a contagem de pedidos atrasados, quando a página a conhece.
    """
    if ativa not in CHAVES:
        raise ValueError(f"Aba desconhecida: {ativa!r}. Use uma de {CHAVES}.")

    itens = []
    for chave, arquivo, rotulo, nome_icone in ABAS:
        if chave == ativa:
            classe, marcacao = "nav-tab active", ' aria-current="page"'
        else:
            classe, marcacao = "nav-tab", ""
        contagem = ""
        if chave == "atrasados" and atrasados:
            contagem = f' <span class="atrasados-count">{atrasados}</span>'
        itens.append(f'            <a href="{arquivo}" class="{classe}"{marcacao}>{icone(nome_icone)} {rotulo}{contagem}</a>')

    corpo = "\n".join(itens)
    return f'<nav class="nav-tabs" aria-label="Navegação do painel">\n{corpo}\n        </nav>'
