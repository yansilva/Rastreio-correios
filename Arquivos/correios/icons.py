"""Conjunto de ícones SVG do painel (traço de 1.75px, 24x24), servido como sprite inline em cada página."""

# Conteúdo interno de cada <symbol>; a cor vem de `currentColor` e o traço do CSS (.icon)
ICONES: dict[str, str] = {
    "package": '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    "bar-chart": '<path d="M5 20v-9M12 20V4M19 20v-6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "truck": '<path d="M3 6h11v10H3zM14 9h4l3 3v4h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "inbox": '<path d="M3 13l3-8h12l3 8v6H3v-6z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "undo": '<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',
    "building": '<path d="M4 21V5l8-2v18M12 9h8v12M4 21h16M8 9h.01M8 13h.01M8 17h.01"/>',
    "sun": (
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'
    ),
    "moon": '<path d="M20 14.5A8.5 8.5 0 019.5 4 8.5 8.5 0 1020 14.5z"/>',
    "refresh": '<path d="M21 12a9 9 0 01-15.5 6.2M3 12A9 9 0 0118.5 5.8"/><path d="M18.5 2v4h-4M5.5 22v-4h4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "map-pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0114 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "alert-triangle": '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4M12 17h.01"/>',
}


def icone(nome: str) -> str:
    """Marcação de um ícone que referencia o sprite (`ICON_SPRITE`) da mesma página."""
    return (
        f'<svg class="icon icon-{nome}" aria-hidden="true" focusable="false">'
        f'<use href="#i-{nome}"></use></svg>'
    )


ICON_SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">'
    + "".join(f'<symbol id="i-{nome}" viewBox="0 0 24 24">{conteudo}</symbol>' for nome, conteudo in ICONES.items())
    + "</svg>"
)
