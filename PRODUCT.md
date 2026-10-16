# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Operador da loja que expede pedidos do Tiny ERP. Trabalha diariamente no painel local, sozinho ou com a equipe de expedição, para saber o que foi enviado, o que está parado e o que está atrasado.

## Product Purpose

Automatiza a consulta de rastreamento dos Correios para os pedidos ativos do Tiny ERP, audita prazos de entrega e permite cotar fretes (SEDEX, PAC, Mini Envios). O sucesso é o operador conseguir identificar e agir sobre atrasos sem conferir pedido a pedido manualmente.

## Positioning

Painel local, sem nuvem própria: roda na máquina do operador, consome diretamente o Tiny ERP e a API oficial dos Correios com credenciais dele, e mostra o estado real dos pedidos com busca instantânea no navegador.

## Operating Context

- Uso diário, em desktop no Windows, iniciado por `ABRIR_PAINEL.bat` (ou `ABRIR_PAINEL.sh` em Unix).
- Atualização automática periódica (a cada 45 min) e atualização manual com cooldown; progresso aparece em tempo real no console SSE.
- Relatórios gerados em HTML (`relatorio_rastreio.html`, `pedidos_atrasados.html`, `opcoes_frete.html`) com alertas visuais e sonoros.

## Capabilities and Constraints

- Busca instantânea client-side por número do pedido (`#123`), cliente, código de rastreio ou cidade.
- Filtros dinâmicos por status (entregue, aguardando retirada, devolvido, em trânsito, atrasado) com contadores.
- Modo claro e escuro, alternância automática pela preferência do sistema e persistência em `localStorage`.
- Servidor HTTP local em `127.0.0.1:8000`; sem backend público e sem autenticação de usuários.
- Interface em português brasileiro. Termos fixos: pedido, rastreio, atrasado, aguardando retirada, frete, prazo.
- Frontend estático sem framework: HTML, CSS e JavaScript em `web/`, servido pelo Python.

## Evidence on Hand

- Painel real em uso com dados de pedidos (`web/`, relatórios HTML na raiz).
- Nenhum case, depoimento ou métrica de uso foi fornecido. Não inventar nenhum.

## Product Principles

- Priorizar o que está atrasado ou parado: o operador deve ver problemas antes de qualquer outra coisa.
- Operar localmente e com as credenciais do próprio operador; nunca expor tokens ou segredos na interface nem nos logs.
- Preferir clareza operacional a expressividade: cada elemento deve ajudar a decidir a próxima ação.
- Manter o painel leve e funcional sem dependências de build no frontend.

## Accessibility & Inclusion

Não há requisito de acessibilidade estabelecido pelo usuário. Como o uso é diário e prolongado, contraste adequado nos modos claro e escuro e estados visíveis de foco são esperados por padrão.
