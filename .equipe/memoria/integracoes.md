# Memória do especialista de integrações — Rastreio-correios

Lições deste projeto. Uma linha por lição, com data.

- 2026-11-25 · Correios: cada evento traz `codigo` e `tipo` separados (`"codigo": "BDE", "tipo": "01"`). A chave usada no código é `BDE/01` (`_MARCAS_POR_CODIGO` em `Arquivos/correios/tracking.py`).
- 2026-11-25 · Armadilha: "Objeto não entregue - ..." contém a palavra ENTREGUE. Por isso BDE/02, BDE/20, BDI/26 viravam entrega. Classificar pelo código primeiro; o texto só é reserva e precisa da negação "NÃO ENTREGUE".
- 2026-11-25 · Retirada e saiu para entrega valem pelo evento de status mais recente. Saiu e retirada ignoram todos os avisos (FC/08 e BDE/19): aviso nunca decide status. Decisão do coordenador, 25/11; antes a retirada ignorava só o aviso de prazo, e um BDE/19 por cima de LDI apagava a retirada.
- 2026-11-25 · Erro de classificação vira registro: `Arquivos/entregas_historico.json` grava entrega a partir de `is_entregue`. O AE16 (AE169600792BR) está lá por causa do bug. Ao corrigir classificação, conferir o histórico e avisar o coordenador; não apagar sem pedido.
- 2026-11-25 · Cache: `Arquivos/rastreios_cache.json` é `{gerado_em, objetos: {rastreio: {eventos: [...]}}}`. Lê-se só com Python local (`python -I`); nunca chamar a API dos Correios nem a do Tiny.
- 2026-11-25 · Antes de mudar classificação, gravar a linha de base do cache (`processar_objeto` por rastreio, em pasta temporária) e comparar depois. A única diferença deve ser a esperada e ela precisa ser explicada no relatório.
- 2026-11-25 · EST/11 ("Favor desconsiderar a informação anterior") desfaz o evento imediatamente anterior no tempo, que é o seguinte na lista, em todas as decisões. O próprio EST/11 não tem marca e conta como status: desfaz a retirada ou a saída logo antes dele. Pedido da revisão de código, via coordenador. No cache: 4 EST/11 em 2 pedidos (AD973626016 e AE048427610); nenhum status muda.
