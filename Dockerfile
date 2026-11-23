# Imagem do painel de rastreio. O código e os dados vêm da pasta do projeto
# (bind mount feito pelo docker-compose.yml); esta imagem só traz Python e dependências.
# Base: Python 3.12.16 sobre Debian trixie, presa pelo digest (a tag 3.12-slim se move a cada release).
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Sao_Paulo

# tzdata: sem ele o TZ não funciona no Debian slim e datetime.now() sairia em UTC.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# Usuário sem privilégios e sem login. Na imagem, o código é de root; com o bind mount do
# docker-compose.yml, o app grava na pasta do projeto (páginas, cache e histórico), então ele
# ALTERA arquivos do projeto. Por isso .git, .equipe e .env entram como somente leitura lá.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Escuta em todas as interfaces IPv4 do container; o docker-compose.yml decide quem alcança a porta do PC.
# ABRIR_NAVEGADOR=0: não há navegador dentro do container.
ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    ABRIR_NAVEGADOR=0

EXPOSE 8000

USER app

CMD ["python", "run.py"]
