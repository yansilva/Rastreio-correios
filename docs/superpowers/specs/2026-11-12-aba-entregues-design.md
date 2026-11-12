# Aba "Entregues" com histórico local de entregas

Data: 2026-11-12 · Autor: coordenador (com o usuário) · Status: aguardando revisão do usuário

## Problema

O operador só vê um pedido entregue até a consulta seguinte (cerca de 45 min). Quando o Tiny marca o pedido como "Entregue", `Arquivos/tiny/orders.py` (`filtrar_pedidos_para_rastreio`) descarta qualquer situação `ENTREGUE` ou `CANCELADO` antes de gerar o CSV. O pedido some do painel e a regra de `deve_ocultar_card` (mantê-lo até sexta às 18h) nunca chega a agir. Não existe lugar para saber o que foi entregue na semana.

## Objetivo e critérios de sucesso

- Uma aba "Entregues" mostra os pedidos entregues na **semana do calendário atual (segunda a domingo)**. Um seletor alterna para a **semana anterior**.
- Cada pedido mostra o **tempo da postagem até a entrega** e a **cidade**. O topo traz um **resumo**: total de entregues, média de dias e pedido mais demorado.
- No **painel principal**, o pedido entregue aparece **só no dia da entrega**.
- Nenhuma chamada extra às APIs, exceto uma última consulta aos Correios por pedido que sai do Tiny (seção 1.3).

## Fora do escopo

- Recuperar as entregas desta semana que sumiram antes desta mudança.
- Exportar a lista ou ver semanas mais antigas que a anterior.
- Filtros e busca dentro da aba. Pode vir depois, se fizer falta.

## 1. Dados (backend)

### 1.1 Arquivo

`Arquivos/entregas_historico.json`, fora do git (entra no `.gitignore`, porque guarda nomes de clientes). É gravado de forma atômica (`.tmp` + `os.replace`), como `correios/cache.py`.

```json
{
  "versao": 1,
  "acompanhados": {"AE123456789BR": {"pedido": "42934", "cliente": "Fulano", "situacao_tiny": "Enviado", "visto_em": "2026-11-12T10:30:00"}},
  "entregas": {
    "AE123456789BR": {
      "pedido": "42934",
      "cliente": "Fulano de Tal",
      "rastreio": "AE123456789BR",
      "cidade": "Rio de Janeiro/RJ",
      "postado_em": "2026-11-07T14:02:00",
      "entregue_em": "2026-11-11T10:15:00",
      "registrado_em": "2026-11-11T10:47:12"
    }
  }
}
```

- A chave é o código de rastreio, e cada entrega é registrada uma vez só (sem duplicar).
- `postado_em` pode ser `null` quando os Correios não trazem o evento de postagem. Nesse caso a contagem de dias fica "—" e o pedido fica fora da média.
- `cidade` é a cidade/UF do evento de entrega. Se ela não vier, usa a cidade do último evento.
- `acompanhados` guarda os pedidos vistos na última consulta real. Ele serve para a seção 1.3.

### 1.2 Módulo `Arquivos/correios/historico_entregas.py`

Funções puras, testáveis sem rede:

- `carregar(caminho) -> dict`: devolve a estrutura vazia se o arquivo não existir ou estiver inválido.
- `salvar(caminho, dados)`: gravação atômica.
- `registrar_entrega(dados, objeto, pedido, cliente)`: registra o pedido se `objeto.status_categoria == "entregue"` e se ele ainda não estiver em `entregas`.
- `podar(dados, agora)`: mantém só as entregas com `entregue_em` na semana ISO atual ou na anterior. A virada de ano usa `isocalendar()`.
- `entregas_da_semana(dados, agora, deslocamento=0)`: devolve a lista da semana atual (0) ou da anterior (-1), da entrega mais recente para a mais antiga.
- `resumo(lista)`: devolve total, média de dias (`postado_em` → `entregue_em`, em dias corridos com uma casa decimal) e o pedido mais demorado.

### 1.3 Integração em `processar()` (`Arquivos/consulta_correios.py`)

- Para todo objeto classificado como entregue, chama `registrar_entrega`, mesmo que o cartão esteja oculto.
- **Só em consulta real** (`usar_cache=False`):
  - Rastreios que estavam em `acompanhados` e não vieram no CSV atual recebem **uma** consulta aos Correios. O token e a função de consulta são os que o `processar()` já usa.
  - Se o resultado for entregue, o pedido é registrado. Em qualquer caso, o rastreio sai de `acompanhados`.
  - Depois disso, `acompanhados` passa a ser o conjunto do CSV atual.
  - Uma falha nessa consulta não interrompe o relatório: o erro vai para o log e o rastreio sai de `acompanhados`.
- Em `usar_cache=True`, nenhuma chamada é feita. Só registra o que já estiver no cache.
- No fim, chama `podar` e depois `salvar`.

### 1.4 Regra do painel (`Arquivos/correios/tracking.py`, `deve_ocultar_card`)

Para `status_categoria == "entregue"`: oculta, salvo se `data_entrega_dt.date() == agora.date()`. Sem data de entrega, oculta, como já acontece hoje. A regra de devolvidos não muda. Atualize a docstring e os testes de `tests/test_correios.py`.

## 2. Página `entregues_semana.html` (frontend)

- É gerada no mesmo `processar()`, por uma função nova, por exemplo `Arquivos/correios/pagina_entregues.py`, para não inchar `consulta_correios.py`. Segue o padrão de template, tokens e ícones das outras páginas.
- **Menu:** a aba "Entregues" entra no menu das três páginas existentes (painel, atrasados e frete, este em `Arquivos/frete/report.py`) e na demo (`Arquivos/demo_data.py`), com `aria-current="page"` quando for a página ativa.
- **Seletor:** "Esta semana (dd/mm–dd/mm)" e "Semana anterior". As duas listas são renderizadas no HTML, e um controle segmentado mostra uma ou a outra (`aria-pressed`). A escolha não é salva.
- **Resumo** de cada semana, no estilo dos cartões de resumo do painel: "N entregues", "Média de X,X dias" e "Mais demorado: #pedido, Y dias". Zero Is Calm: semana vazia fica sem números zerados e com a mensagem "Nenhuma entrega nesta semana".
- **Lista:**
  - Desktop: tabela com Pedido, Cliente, Rastreio (com botão "Copiar rastreio"), Cidade, Postado em, Entregue em e Dias.
  - Celular (≤640px): cartões.
  - Ordem: da entrega mais recente para a mais antiga.
  - "Dias" acima de 7 recebe o tom de aviso já usado em atrasados, sem verde para "rápido" (One Meaning Per Color).
- **Acessibilidade:** tabela com `<th scope>`, foco visível, alvos de 44px no celular e contraste de 4,5:1.
- **Servidor:** incluir `entregues_semana.html` na lista de permissão de páginas de `Arquivos/server/security.py`. Sem isso, ela responde 404.
- Atualizar o `DESIGN.md` com a nova página.

## 3. Testes

- `historico_entregas`:
  - registro sem duplicar;
  - não registra quem não está entregue;
  - poda das semanas antigas;
  - semana anterior;
  - virada de ano (semana 1 contra semana 52/53);
  - resumo com e sem `postado_em`;
  - arquivo ausente ou corrompido.
- `processar()`:
  - rastreio que saiu do CSV recebe uma consulta (mockada) e entra no histórico se estiver entregue;
  - com `usar_cache=True`, nenhuma consulta é feita;
  - falha da consulta não derruba o relatório.
- Regra do painel: entregue hoje aparece; entregue ontem fica oculto.
- Página:
  - gerada com as duas semanas;
  - vazio sem zeros;
  - aba no menu das quatro páginas;
  - servidor responde 200 para `entregues_semana.html`.

## 4. Execução pela equipe

1. **backend:** seções 1.1 a 1.4, mais o `.gitignore` e a lista de permissão do servidor.
2. **frontend:** seção 2, em paralelo com o backend. Usa o contrato da 1.1 e as funções da 1.2, que podem ser simuladas nos testes até o backend terminar.
3. **qa** e **acessibilidade** validam no navegador. **revisao-codigo** revisa o diff.
4. O coordenador reinicia o servidor, confere e pede o aval do commit ao usuário.
