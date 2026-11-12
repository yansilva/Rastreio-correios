# Memória — revisao-codigo (Rastreio-correios)

- 2026-11-12 · Páginas geradas (`*.html` na raiz) não são versionadas; o CI (`.github/workflows/ci.yml`, ubuntu, `pytest tests/`) roda sem elas. Teste que pede ao servidor um HTML gerado só passa localmente. Confirmar com `ServerConfig(base_dir=Path(tempdir))` (base_dir precisa ser `Path`, não `str`).
- 2026-11-12 · `relatorio_rastreio.html` tem rota própria (`_serve_main_html`); as demais páginas passam por `_serve_static_file`, que exige o arquivo no disco. A lista de permissão de `security.py` já aceita qualquer `.html` na raiz.
- 2026-11-12 · Os testes de `processar()` em `tests/test_regerar.py` usam `patch.object(consulta_correios, "__file__", ...)` com pasta temporária: tudo que `processar()` grava vai para lá, não para a raiz do repo.
- 2026-11-12 · No reteste, conferir também se o teste novo é estreito: asserções do tipo "X not in arquivo inteiro" (ex.: `"aria-label" not in app_js`) viram trava para mudanças futuras sem relação.
- 2026-11-12 · No PowerShell, script Python com aspas duplas passado por here-string pode quebrar o parser; prefira `pytest arquivo::Classe` para rodar um teste sozinho.
