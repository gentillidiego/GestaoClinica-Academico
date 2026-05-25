# Gestão Clínica

Plataforma de acompanhamento e sistemas Python/Flask com gerador robusto de boletos médicos e receitas via PDF.

## 🐳 Arquitetura e Deploy (Docker)

O sistema foi inteiramente migrado para uma arquitetura moderna baseada em microsserviços via Docker Compose, substituindo o antigo banco SQLite e execução via PM2. 
A stack atual roda com:
- **gestaoclinica (Flask via Gevent)** - Servidor Web focado em concorrência. Trabalhando na porta `5002`.
- **gestaoclinica-postgres (PostgreSQL 16)** - Banco de dados de produção robusto gerenciando todos os dados transacionais de pacientes e clínicas.
- **gestaoclinica-redis (Redis 7)** - Broker de mensagens em background e backend do limitador de taxa (*Rate Limiting*).
- **gestaoclinica-celery (Celery Worker)** - Fila de processos responsável pela geração super pesada de PDFs (Receitas/Atestados) em segundo plano usando a biblioteca nativa `WeasyPrint`.

> **Fonte de dados ativa:** PostgreSQL é o banco oficial da aplicação. Arquivos `clinica.db` existentes no repositório são legado/backup da migração e não devem ser montados pelos contêineres web ou worker.

> **Variáveis obrigatórias:** configure `.env` com `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` e `POSTGRES_PASSWORD`. Para uma checagem rápida do ambiente, execute `python scripts/check_env.py`.

> 🛠️ **Volumes Persistentes:** O volume `postgres_data` do banco de dados relacional (PostgreSQL) e o volume interno `pdf_temp` dos PDFs temporários estão preservados. Caso haja a reconstrução dos contêineres e imagens, não haverá exclusão acidental de dados ou documentações ativas de nenhum usuário clínico/paciente.

### 📝 Últimas Atualizações Críticas (Sprints & Defeitos)

1. **Impactos da Tipagem Forte do PostgreSQL:** Ao migrarmos do SQLite, fomos da formatação relaxada para tipagens muito estritas e lógicas. Diante disso:
   - Os marcadores de formatação DML no banco passaram estritamente da representação universal SQLite de `?` para os placeholders psycopg2 `%s` em `python`.
   - O objeto temporal lido e entregue pelas colunas lógicas (`data`, `criado_em`, `data_assinatura`) passou de texto puro (*string*) para a classe oficial `datetime.datetime` do Python/PostgreSQL.
   - **Solução de Falha Interna 500 no Front-end (Jinja Template):** O antigo uso descuidado do fatiamento/manipulação direta no Python/Jinja (`ex: {{ paciente.criado_em.split(' ')[0] }}`) desencadeou cascatas de telas de `Internal Server Error 500`. Corrigimos dezenas de ocorrências na Interface inserindo filtragem e serialização de cast como obrigatórias (`ex: {{ (paciente.criado_em|string).split(' ')[0] }}`).

2. **Acoplamento do Celery - Configuração Final PDF:**
   - Detectamos e corrigimos ausências de tarefas durante as conexões em tempo real - a inicialização foi obrigatoriamente forçada dentro de `celery_app.py` com o vínculo `include=['tasks.pdf_tasks']`, ensinando o operário central Python as rotinas disponíveis para geração.
   - Havia silos estáticos isolados: A Aplicação Flask não conseguia achar o PDF que o Trabalhador enviou como pronto, pois não enxergavam a mesma pasta real da máquina. Passamos então a conectar inteligentemente os diretórios sob a tag global Docker *Volume* (`pdf_temp:/app/pdf_temp`) entre o Web App e o serviço Celery. Agora os relatórios aparecem num estalar de dedos de forma perfeita com acesso livre compartilhado.

## 🦸 Instruções Ouro para Desenvolvedores e IAs (Agente Antigravity / Eng. de Sistema)

Você, como próximo dev, mantenedor ou IA, deve assumir este repositório aplicando estas métricas mandatórias:

1. **Fluxo Estrito de Deploy (Builds Obrigatórios):**
   Os arquivos primários da aplicação em Produção (views, serviços `python`, estilos css, estruturas html em `templates`) **não operam sob bind de Volumes/Live Reload do Host**. Eles estão congelados dentro do binário original da imagem compilada na VPS base por um reflexo das boas práticas Docker.
   - **Toda e Qualquer Alteração Injetada Via Console/Editor:** Se efetuarmos o refatoramento de um bug pontual (`ex: arruma o botão do javascript e dá refresh`), o sistema rodante jamais vai aplicar isso instantânea e magicamente. Você deve instruir e reestruturar o contêiner por meio de um build contínuo (no seu backend local) para substituir a versão operante de produção:
     ```bash
     # Aplicando Modificações nos Flask Blueprints e FrontEnd
     docker compose build gestaoclinica && docker compose up -d gestaoclinica
     
     # Se você modificou ou evoluiu o gerador Worker/RabbitMQ:
     docker compose build celery-worker && docker compose up -d celery-worker
     ```

2. **Tratamento de Strings x Datetime (Templates Jinja Ocasionalmente Frágeis):**
   Se o log disser `TypeError: 'datetime.datetime' object is not subscriptable` ou `TypeError: argument of type 'datetime.datetime' is not iterable` na leitura de logs web `docker logs gestaoclinica-docker`, verifique sua template HTML. Operações como `split()` ou injeções lógicas (`' ' in data`) falham diretamente no objeto. Converta ativamente seu objeto em manipulação para `.str() / |string` (ex: `(paciente.criado_em|string)`) e, em seguida, manipule a data ao seu agrado. 

3. **Escopo Escravo de Arquivos (Em Background):**
   Ao idealizar processos paralelos e criar arquivos binários no container `A` (Worker/Machine Learnings) que devem ser mostrados pela porta do container web `B`, declare um nome em Volume Global em `docker-compose.yml` e acople nos dois! Rotas cegas disparam Status Codes de redirecionamentos vazios ou Erro `404` caso os diretórios reais não se entrelacem.

4. **Escalando o Stress na Carga (Rate Limits 429):**
   Este aplicativo obedece métricas rígidas de estrangulamento de tentativas e injeção (Graças ao `Flask-Limiter` vinculado ao BD Redis). Operações com Locust ou artilharias de bot (Ex: Testes Assíncronos `simulando 100 usuários efetuando login de uma vez`) irão engasgar rapidamente com status `HTTP 429`. Afrouxe ou remova os limites estritamente dentro de `.env` ou do código de `auth.py` caso procure conduzir Testes de Escalabilidade controlados, lembrando categoricamente de devolvê-los assim que os dados analíticos terminarem seu ciclo!
