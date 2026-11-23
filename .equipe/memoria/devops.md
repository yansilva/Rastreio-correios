# Memória do devops — Rastreio-correios

- 2026-11-23 · O servidor recusa o cabeçalho Host quando a porta não é a `SERVER_PORT` (`host_permitido`). Em Docker, a porta publicada no PC tem de ser a mesma do container (8000). Testar em outra porta exige `Host` sem porta ou com a porta do container.
- 2026-11-23 · A imagem precisa de `tzdata` (Debian slim) e de `TZ=America/Sao_Paulo`. Confirmado: o container responde `-03`.
- 2026-11-23 · `.dockerignore` deve excluir `.env` e as páginas/dados gerados. O código e os dados chegam pelo bind mount `.:/app`, então o `.env` é lido da pasta sem entrar na imagem.
- 2026-11-23 · `processar(usar_cache=True)` reescreve `entregas_historico.json` e poda entregas antigas. Antes de testar, copie os dados da pasta `Arquivos/` e restaure depois.
- 2026-11-23 · Para testar o compose sem derrubar a instância da 8000, use um override em `scratchpad` com `ports: !override` e a porta de teste. Derrube com o mesmo `-f` ao final.
- 2026-11-23 · No PowerShell 5.1, aspas duplas dentro de `docker run ... sh -c "..."` são perdidas. Para rodar Python no container, envie o script por stdin (`... python -`).
- 2026-11-23 · `ABRIR_NAVEGADOR=0` é o interruptor do navegador. Padrão 1, para não mudar o comportamento fora do Docker.
- 2026-11-23 · `ports: "8000:8000"` no Docker Desktop também publica em `[::]:8000`. Use `"0.0.0.0:8000:8000"` (IPv4) ou `127.0.0.1:8000:8000`. Com Docker, o IP de origem vira o gateway 172.x, então a checagem de IP não limita acesso. Teste IPv6 global com `curl.exe -g`, esperando exit 7.
- 2026-11-23 · Bind mount grava no projeto: `.git`, `.equipe` e `.env` entram como `:ro`. Comentário do Dockerfile não pode dizer que o código fica protegido.
- 2026-11-23 · `.dockerignore`: padrões sem `**/` só casam na raiz (o CSV de clientes entrou na imagem). Use `**/.env`, `**/*.csv`, `**/*.json`.
- 2026-11-23 · Para mandar script ao `docker exec -i`, o stdin do PowerShell tem BOM e o `sh` falha com "test: not found". Use `docker exec ... sh -c "..."` com aspas duplas.
- 2026-11-23 · `requirements.txt` com versões fixas: `requests==2.34.2`, `python-dotenv==1.2.4` (verificado no pip). As dependências indiretas ainda não estão fixas.
- 2026-11-23 · Base fixada por digest: `python:3.12-slim@sha256:5e2bdb1b…` (Python 3.12.16, Debian trixie).
