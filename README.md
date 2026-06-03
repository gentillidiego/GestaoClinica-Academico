# Gestão Clínica

Sistema web para gestão de prontuários odontológicos em clínica-escola, com cadastro de pacientes, anamneses, exames, plano de tratamento, evolução clínica, assinaturas de validação e geração de documentos em PDF.

O projeto usa Flask com renderização server-side, PostgreSQL como banco transacional, Redis para cache, sessões, filas e rate limiting, Celery para tarefas em background e Docker Compose para execução local ou em servidor.

## Status do Projeto

- Branch principal: `main`
- Repositório remoto: `git@github.com:gentillidiego/GestaoClinica-Academico.git`
- Banco oficial: PostgreSQL
- Banco SQLite local (`clinica.db`): legado de migração, não deve ser usado em produção
- Documentação técnica atual: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Guia de desenvolvimento e operação: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## Principais Recursos

- Autenticação com perfis de acesso: administrador, professor, aluno e atendimento.
- Cadastro e acompanhamento de pacientes.
- Anamnese, exame físico, odontograma, periograma e controle de placa.
- Plano de tratamento com aprovação por professor.
- Evolução clínica vinculada aos procedimentos aprovados.
- Assinaturas por login/senha para professor e aluno executor.
- Assinatura digital do paciente nos fluxos que exigem consentimento.
- Receituários e atestados odontológicos em PDF via WeasyPrint.
- Geração assíncrona de PDFs por Celery.
- Health check em `/health`.
- Rate limiting com Flask-Limiter e Redis.

## Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3.11, Flask 3.0 |
| Servidor WSGI | Gunicorn com worker `gevent` |
| Banco de dados | PostgreSQL 16 |
| Cache, sessões e filas | Redis 7 |
| Tarefas assíncronas | Celery 5 |
| PDFs | WeasyPrint |
| Frontend | Jinja2, CSS e JavaScript sem framework |
| Infraestrutura | Docker, Docker Compose |

## Estrutura do Repositório

```text
.
├── app.py                  # Factory da aplicação Flask
├── database.py             # Pool PostgreSQL e helpers de query
├── blueprints/             # Rotas e fluxos funcionais
├── services/               # Serviços de domínio e apoio
├── tasks/                  # Tarefas Celery
├── templates/              # Templates Jinja2
├── static/                 # CSS, JS e imagens
├── scripts/                # Scripts operacionais
├── tests/                  # Testes de carga e apoio
├── docs/                   # Documentação para handoff técnico
├── docker-compose.yml      # Stack local/servidor
└── Dockerfile              # Imagem da aplicação
```

## Configuração Inicial

Pré-requisitos:

- Docker e Docker Compose
- Git
- Python 3.11, apenas se for executar scripts fora do contêiner

Crie o arquivo de ambiente:

```bash
cp .env.example .env
```

Preencha ao menos:

```env
SECRET_KEY=gere-uma-chave-forte
DATABASE_URL=postgresql://clinica_user:sua_senha@postgres:5432/clinica
REDIS_URL=redis://redis:6379/0
POSTGRES_PASSWORD=sua_senha
ADMIN_USERNAME=admin
ADMIN_PASSWORD=troque-esta-senha
```

Para gerar uma chave segura:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Execução com Docker

Suba a stack:

```bash
docker compose up -d --build
```

Verifique os serviços:

```bash
docker compose ps
docker compose logs -f gestaoclinica
```

A aplicação fica disponível em:

```text
http://localhost:5002
```

Crie o usuário administrador inicial:

```bash
docker compose exec gestaoclinica python create_admin.py
```

Valide as dependências de ambiente:

```bash
docker compose exec gestaoclinica python scripts/check_env.py
```

## Rotina de Deploy

O código da aplicação fica dentro da imagem Docker. Alterações em Python, templates, CSS ou JavaScript exigem rebuild do serviço correspondente.

Aplicação web:

```bash
docker compose build gestaoclinica
docker compose up -d gestaoclinica
```

Worker Celery:

```bash
docker compose build celery-worker
docker compose up -d celery-worker
```

Banco, Redis e volumes persistentes não devem ser removidos durante atualizações comuns.

## Dados e Segurança

- Nunca versionar `.env`, bancos locais, backups, logs, cookies, PDFs temporários ou resultados de teste de carga.
- `clinica.db` e backups SQLite são legado de migração.
- `postgres_data`, `redis_data` e `pdf_temp` são volumes persistentes da stack Docker.
- `create_admin.py` usa `ADMIN_USERNAME` e `ADMIN_PASSWORD`; não há senha hardcoded.
- O rate limit de login está ativo e usa Redis como backend.
- Operações clínicas sensíveis devem manter validação por perfil e, quando aplicável, por login/senha do professor ou aluno executor.

## Comandos Úteis

```bash
# Compilar módulos Python
python3 -m compileall app.py blueprints services tasks scripts

# Ver status do Git
git status --short --branch

# Logs da aplicação
docker compose logs -f gestaoclinica

# Logs do worker
docker compose logs -f celery-worker

# Health check
curl http://localhost:5002/health
```

## Desenvolvimento

Leia [CONTRIBUTING.md](CONTRIBUTING.md) antes de alterar o projeto.

Pontos de atenção:

- As queries usam SQL direto com `psycopg2`; use placeholders `%s`.
- Datas vindas do PostgreSQL podem chegar ao Jinja como `datetime`; converta para string antes de usar `split`, slicing ou operadores de texto.
- PDFs gerados por WeasyPrint devem usar CSS simples e previsível para impressão.
- Se um arquivo criado pelo Celery precisa ser servido pelo Flask, use volume compartilhado.
- Mudanças em arquitetura, ambiente, deploy, segurança, banco, permissões, PDFs ou fluxos clínicos devem atualizar a documentação no mesmo ciclo.
