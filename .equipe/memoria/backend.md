# Memória do backend — Rastreio-correios

- 2026-11-12 · Erro meu: escrevi `datetime(2026, 11, 5, 24)` num teste; hora 24 não existe. Use `0` do dia seguinte.
- 2026-11-12 · Padrão do projeto: testes que chamam `consulta_correios.processar()` patcham `consulta_correios.__file__` para uma pasta temporária `Arquivos/`, assim nada é gravado no repositório. Arquivos de estado novos devem ficar na mesma pasta do script, calculados a partir de `__file__`.
- 2026-11-12 · Padrão do projeto: o ruff (isort) exige que um import novo do pacote `correios` entre no bloco `from correios import (...)` em ordem alfabética, e não como linha separada.
- 2026-11-12 · Padrão do projeto: `processar()` trata exceções com `print` (ex.: "Aviso: ..."), não com `logging`. Mantenha o estilo.
- 2026-11-12 · Correção pedida pelo coordenador (QA bloqueante): validar cada entrada de dados lidos do JSON, e não só a raiz. `carregar()` descarta entrada sem data válida e registra aviso; `podar` e `entregas_da_semana` também ignoram entrada incompleta, para não derrubar `processar()`.
- 2026-11-12 · Correção pedida pelo coordenador: o `processar()` não tem `try/except ImportError` para módulos do próprio projeto; import direto. Falha ao gerar uma página secundária vira aviso com `print`, e não devolve False.
