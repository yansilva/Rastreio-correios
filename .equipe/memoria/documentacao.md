# Memória do documentacao — Rastreio-correios

- 2026-11-25 · Status de Correios só se documenta em `PRODUCT.md` (termos e filtros) e `docs/architecture.md` (seção 3.3.1, regras). O `README.md` só cita o tema de passagem; não duplicar a regra lá.
- 2026-11-25 · `docs/superpowers/` (specs e planos de 12/11) é histórico: não reescrever. Só a documentação viva (README, PRODUCT, architecture) entra na revisão.
- 2026-11-25 · Regra ainda não implementada (ex.: "Saiu para entrega") se escreve com marca "(previsto)" ou "Pendente". Quando o código entrar, tire a marca na mesma rodada, senão a doc afirma o que não existe.
- 2026-11-25 · Não detalhar cor, ícone e texto exato da pílula de filtro: são do designer (`DESIGN.md` e brief). Na doc, basta dizer que existe filtro próprio.
- 2026-11-25 · Já desatualizado e fora do escopo de status: `architecture.md` não cita Docker, `launcher.py` nem a aba Entregues; `PRODUCT.md` não cita a aba Entregues. Registrar ao coordenador antes de mexer.
- 2026-11-25 · Divergência código × doc (resolvida pelo backend): na retirada, o código ignorava só o aviso de prazo. Agora qualquer aviso (FC/08, BDE/19) é ignorado, igual ao saiu para entrega. Na 3.3.1 a regra precisa dizer "qualquer aviso", não só "avisos".
- 2026-11-25 · Classificação agora é pelo código `codigo/tipo` (`marcas_do_evento` em `tracking.py`), com o texto só como reserva. Quando a doc cita código, conferir o mapa `_MARCAS_POR_CODIGO`; ele é a fonte, não a doc.
- 2026-11-25 · Antes de tirar uma marca de "previsto" ou "Pendente", rodar os testes do assunto (`tests/test_saiu_para_entrega.py` e `tests/test_correios.py`, 54 passam) e conferir a pílula em `consulta_correios.py`. O texto da nota do peer não basta.
