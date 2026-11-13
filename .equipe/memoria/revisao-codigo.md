# Memória — revisao-codigo (Rastreio-correios)

- 2026-11-12 · Páginas geradas (`*.html` na raiz) não são versionadas; o CI (`.github/workflows/ci.yml`, ubuntu, `pytest tests/`) roda sem elas. Teste que pede ao servidor um HTML gerado só passa localmente. Confirmar com `ServerConfig(base_dir=Path(tempdir))` (base_dir precisa ser `Path`, não `str`).
- 2026-11-12 · `relatorio_rastreio.html` tem rota própria (`_serve_main_html`); as demais páginas passam por `_serve_static_file`, que exige o arquivo no disco. A lista de permissão de `security.py` já aceita qualquer `.html` na raiz.
- 2026-11-12 · Os testes de `processar()` em `tests/test_regerar.py` usam `patch.object(consulta_correios, "__file__", ...)` com pasta temporária: tudo que `processar()` grava vai para lá, não para a raiz do repo.
- 2026-11-12 · No reteste, conferir também se o teste novo é estreito: asserções do tipo "X not in arquivo inteiro" (ex.: `"aria-label" not in app_js`) viram trava para mudanças futuras sem relação.
- 2026-11-12 · No PowerShell, script Python com aspas duplas passado por here-string pode quebrar o parser; prefira `pytest arquivo::Classe` para rodar um teste sozinho.
- 2026-11-13 · Quando uma fila ganha vários leitores, conferir se a antiga ainda tem quem leia: fila sem leitor fica cheia e mantém o caminho "cheia" sempre ativo. Teste de corrida: script com 4 threads e `maxsize=2` no scratchpad.
- 2026-11-13 · O `CorreiosClient.consultar_objeto` embrulha os erros do `requests` em `CorreiosError`, mas a nova tentativa após 401 (client.py:158) chama `requests.get` sem embrulhar: o `except` estreito precisa dos dois.
- 2026-11-13 · `CorreiosClient.consultar_objeto` só renova o token após um 401 quando recebe `token=None`; com o token explícito, um 401 vira `CorreiosAuthError`. Conferir isso sempre que mexerem em token ou em cliente.
- 2026-11-13 · Ao trocar `requests.get` direto por `TinyClient`, comparar timeout e novas tentativas: o pior caso de tempo muda (30 s × 3 tentativas contra 15 s × 1).
- 2026-11-13 · Renovação de token: além de "renova uma vez", contar as chamadas da rodada inteira depois da renovação. Quem chama pode continuar passando o token velho, e cada item passa a custar 2 requisições. Também testar um cliente novo, sem token guardado. Script: `scratchpad/renovacao_token.py`.
- 2026-11-13 · Campo de diagnóstico que guarda `str(exc)`: conferir se a exceção leva a causa real. `FreteServicoIndisponivelError` (frete/client.py, 400/422) descarta o corpo da resposta, então o motivo vira só "HTTP 400".
- 2026-11-13 · CSS: quando uma media query passa a cobrir tudo acima de 640px e a ≤640 redeclara a mesma regra, a regra base fica morta. Procure a regra base sempre que mexerem nos limites das media queries.
