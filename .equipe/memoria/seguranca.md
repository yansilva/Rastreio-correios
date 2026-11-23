# Lições de segurança neste projeto

- 2026-11-23 · Docker Desktop (Windows) troca o IP de origem pelo gateway da rede Docker (172.x): `ip_na_rede_local` deixa de proteger. Host e Origin são controlados por quem não usa navegador; só valem contra navegador (rebinding/CSRF).
- 2026-11-23 · Porta publicada sem IP (`"8000:8000"`) abre também `[::]:8000`. O PC tem IPv6 global (2804:…); testar sempre com `curl -H "Host: 127.0.0.1:8000" http://[IPv6-global]:8000/api/status`. `"0.0.0.0:8000:8000"` publica só IPv4 (testado).
- 2026-11-23 · `.dockerignore` sem `**/` só casa na raiz do contexto: conferir a imagem com `docker run --rm --entrypoint sh IMAGEM -c "find /app"`.
- 2026-11-23 · Bind mount no Docker Desktop é 9p/drvfs sem permissões: `USER app` não impede escrever em código, `.env` e `.git/hooks` da pasta montada.
- 2026-11-23 · `/regerar` não é só leitura: reescreve `Arquivos/entregas_historico.json` e pode tirar entregas antigas. Para provar que o container consegue regerar sem chamar a rota, conferir com `test -w` as 5 saídas da raiz e a pasta `Arquivos/`.
- 2026-11-23 · O Wi-Fi deste PC está com perfil Público, e python.exe e com.docker.backend.exe têm regra de entrada liberada no Público, qualquer porta.
