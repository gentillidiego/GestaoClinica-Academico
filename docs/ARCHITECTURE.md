# Arquitetura

Este documento descreve a arquitetura atual do Gestão Clínica para facilitar manutenção por outra equipe de desenvolvimento.

## Responsável Técnico

Desenvolvimento por **Gentilli Pereira** - Analista e adm de sistemas, desenvolvedor de Software. Atua no desenvolvimento de aplicações web, arquitetura de sistemas e gerenciamento de infra Linux.

- E-mail: `gentillidiego@gmail.com`
- Telefone/WhatsApp: `(82) 98179-5886`

O projeto é proprietário. Uso, cópia, modificação, distribuição ou transferência para terceiros dependem de autorização prévia e expressa de Gentilli Pereira.

## Visão Geral

O sistema é uma aplicação Flask monolítica, modularizada por blueprints e serviços de domínio. A renderização é server-side com Jinja2. O banco oficial é PostgreSQL, acessado por SQL direto via `psycopg2`. Redis centraliza cache, sessões, rate limiting e fila Celery. PDFs são gerados com WeasyPrint, preferencialmente em background.

## Componentes

| Componente | Responsabilidade |
| --- | --- |
| `gestaoclinica` | Aplicação Flask servida por Gunicorn/Gevent na porta `5002` |
| `postgres` | Banco relacional transacional e fonte oficial dos dados clínicos |
| `redis` | Cache, sessões server-side, broker/backend do Celery e rate limiting |
| `celery-worker` | Processamento assíncrono, principalmente geração de PDFs |

## Fluxo de Requisição

1. O usuário acessa a aplicação Flask.
2. Flask-Login valida a sessão.
3. As rotas nos blueprints consultam ou alteram dados pelo helper `database.py`.
4. Templates Jinja2 renderizam a interface.
5. Quando necessário, a aplicação delega geração de PDF para Celery.
6. O worker grava o arquivo em `pdf_temp`, volume compartilhado com a aplicação web.

## Módulos Principais

| Caminho | Função |
| --- | --- |
| `app.py` | Cria e configura a aplicação, extensões, sessão Redis, logging e blueprints |
| `database.py` | Inicializa o pool PostgreSQL e concentra helpers `query`, `execute` e transações |
| `extensions.py` | Instâncias compartilhadas de Limiter e Cache |
| `blueprints/auth.py` | Login, logout e rate limit de autenticação |
| `blueprints/admin.py` | Gestão de usuários e perfis |
| `blueprints/patients.py` | Cadastro, prontuário, plano de tratamento e evolução clínica |
| `blueprints/exams.py` | Exames clínicos, odontograma, periograma e controle de placa |
| `blueprints/documents.py` | Receituários, atestados e orquestração de PDFs |
| `services/periodontal_diagnosis.py` | Cálculo de diagnóstico periodontal conforme classificação AAP 2018 |
| `tasks/pdf_tasks.py` | Tarefas Celery de geração de PDF |

## Banco de Dados

O projeto não usa ORM. Toda consulta deve ser parametrizada com placeholders do `psycopg2`:

```python
query("SELECT * FROM users WHERE username = %s", (username,), one=True)
```

Não use `?`, que era o placeholder do SQLite legado.

As tabelas são criadas e atualizadas por `init_db()` em `database.py`. Como não há Alembic ou outro migrador, novas colunas precisam ser adicionadas de forma idempotente, usando `_ensure_columns_exist()` ou padrão equivalente.

## Regras de Negócio Sensíveis

- O TCLE deve bloquear fluxos clínicos quando o paciente ainda não assinou o consentimento exigido.
- Validações de professor devem permanecer vinculadas a perfil autorizado e autenticação por senha.
- Procedimentos aprovados no plano de tratamento são enviados para evolução clínica conforme a regra implementada no backend.
- Registros clínicos assinados devem ter edição bloqueada ou estritamente controlada.
- Exclusões clínicas devem preservar validação por perfil e confirmação de senha quando aplicável.

## PDFs

Os PDFs usam WeasyPrint. Para reduzir falhas de impressão:

- Prefira CSS simples, com tamanhos, margens e tabelas explícitas.
- Evite dependência de fontes externas.
- Teste qualquer alteração em `templates/pdfs/`.
- Use `pdf_temp` para arquivos temporários compartilhados entre web e worker.

## Observabilidade

- `/health` retorna status da aplicação e conectividade com o banco.
- Logs da aplicação são emitidos no stdout do Gunicorn e em `logs/app.log` quando fora de debug.
- Logs do Docker devem ser a primeira fonte de diagnóstico em produção.

## Decisões Arquiteturais

- SQL direto foi mantido para preservar compatibilidade com a base existente e facilitar leitura por equipes que dominam SQL.
- Redis é usado como infraestrutura compartilhada para evitar contadores ou sessões isoladas por worker.
- Celery isola tarefas lentas e evita bloquear workers web durante geração de PDFs.
- Docker Compose é suficiente para o estágio atual do projeto e mantém o ambiente reprodutível.
