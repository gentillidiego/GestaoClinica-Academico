# Desenvolvimento e Operação

Este guia descreve o fluxo recomendado para desenvolvimento, validação e operação do Gestão Clínica.

## Ambiente

1. Copie `.env.example` para `.env`.
2. Preencha `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `POSTGRES_PASSWORD`, `ADMIN_USERNAME` e `ADMIN_PASSWORD`.
3. Suba a stack:

```bash
docker compose up -d --build
```

4. Crie o administrador inicial:

```bash
docker compose exec gestaoclinica python create_admin.py
```

5. Valide ambiente e conectividade:

```bash
docker compose exec gestaoclinica python scripts/check_env.py
```

## Desenvolvimento Local

Quando desenvolver fora do Docker, crie uma venv e instale as dependências:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Garanta que `DATABASE_URL` e `REDIS_URL` apontem para serviços acessíveis no ambiente local.

## Validação Antes de Enviar

Execute pelo menos:

```bash
python3 -m compileall app.py blueprints services tasks scripts
```

Quando a alteração envolver Docker, rode:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Quando a alteração envolver autenticação, permissões, exclusões, assinaturas, PDFs ou banco de dados, faça teste manual do fluxo afetado.

## Convenções de Código

- Mantenha rotas nos blueprints e regras reutilizáveis em `services/`.
- Use SQL parametrizado com `%s`.
- Não concatene valores do usuário em SQL.
- Prefira transações explícitas com `execute_transaction()` quando uma operação depender de múltiplos comandos.
- Ao adicionar colunas, atualize `init_db()` e adicione migração idempotente.
- Evite lógica complexa dentro de templates Jinja.
- Para campos temporais no Jinja, converta antes de operar como texto:

```jinja2
{{ (paciente.criado_em|string).split(' ')[0] }}
```

## Deploy

O projeto não usa bind mount do código-fonte em produção. Depois de alterar código, templates ou assets, reconstrua a imagem.

Aplicação web:

```bash
docker compose build gestaoclinica
docker compose up -d gestaoclinica
```

Worker:

```bash
docker compose build celery-worker
docker compose up -d celery-worker
```

## Backup e Dados

- Faça backup do PostgreSQL antes de alterações de schema.
- Não remova volumes `postgres_data`, `redis_data` ou `pdf_temp` sem plano de recuperação.
- Arquivos SQLite e backups antigos são legado e não devem ser fonte de verdade.
- Nunca envie `.env`, logs, cookies, bancos locais, backups ou PDFs temporários para o Git.

## Diagnóstico

Verificar containers:

```bash
docker compose ps
```

Logs da aplicação:

```bash
docker compose logs -f gestaoclinica
```

Logs do worker:

```bash
docker compose logs -f celery-worker
```

Health check:

```bash
curl http://localhost:5002/health
```

Checagem de ambiente dentro do container:

```bash
docker compose exec gestaoclinica python scripts/check_env.py
```

## Teste de Carga

O arquivo `tests/locustfile.py` pode ser usado com Locust:

```bash
locust -f tests/locustfile.py --host=http://localhost:5002
```

Abra `http://localhost:8089` e configure a quantidade de usuários simulados. Durante testes de carga, avalie o impacto dos limites HTTP 429 e restaure os limites normais após a coleta.
