# Documentação Técnica e de Arquitetura: Gestão Clínica Acadêmica (UMJ)

Este documento destina-se ao Departamento de Tecnologia da Informação (TI) da UMJ. Ele detalha a arquitetura de software, infraestrutura, persistência de dados, dependências e diretrizes de segurança do sistema de Gestão Clínica Odontológica.

---

## 1. Visão Geral da Arquitetura

O sistema foi arquitetado como uma aplicação web moderna, conteinerizada e dividida em microsserviços. O design prioriza a alta disponibilidade, tolerância a falhas e isolamento de processos pesados (como geração de relatórios PDF).

**Stack Tecnológica:**
- **Linguagem Principal:** Python 3.11
- **Framework Web:** Flask 3.0.3
- **Servidor WSGI:** Gunicorn operando com *Gevent* (processamento assíncrono para lidar com I/O sem travar o servidor)
- **Banco de Dados Relacional:** PostgreSQL 16
- **Message Broker & Cache:** Redis 7
- **Processamento Assíncrono:** Celery (Workers independentes)
- **Infraestrutura / Orquestração:** Docker & Docker Compose

---

## 2. Topologia de Contêineres (Docker)

O ambiente de produção opera sob uma rede virtual isolada (tipo *bridge*) configurada via `docker-compose.yml`, englobando 4 serviços principais:

1. **`gestaoclinica-web` (Web App):**
   - **Responsabilidade:** Receber e processar requisições HTTP, gerenciar a API do painel administrativo, rotas e servir os templates do front-end.
   - **Porta Mapeada Host:** `5002` (Mapeia para 5002 interno).

2. **`gestaoclinica-postgres` (Banco de Dados):**
   - **Responsabilidade:** Única fonte de verdade persistente. Armazena usuários, planos de tratamento, evoluções clínicas, odontogramas lógicos, etc.
   - **Porta Mapeada Host:** `5432` (isolado na rede Docker para segurança, mapeado apenas se necessário para debug).

3. **`gestaoclinica-redis` (Mensageria e Rate Limiter):**
   - **Responsabilidade:** Funciona como corretor de mensagens (Message Broker) entregando tarefas pesadas da web para os workers. Também atua limitando conexões agressivas (Rate Limiting via `Flask-Limiter`).
   - **Porta Padrão:** `6379`.

4. **`gestaoclinica-celery` (Background Worker):**
   - **Responsabilidade:** Consumir processos da fila do Redis e executá-los em plano de fundo sem penalizar o usuário final. Principal função atual: **Gerar PDFs densos** usando o motor WeasyPrint.

---

## 3. Gestão e Persistência de Dados (Volumes)

Para garantir a total integridade de dados (Stateful) em um ambiente efêmero (Stateless), o Docker foi parametrizado com os seguintes volumes externos persistentes ao sistema operacional do servidor (Host):

- **`postgres_data`**: Mapeia o diretório interno `/var/lib/postgresql/data` garantindo que o banco de dados não seja perdido em caso de deleção de imagem/container.
- **`uploads`** *(bind mount)*: Mapeamento de diretório da aplicação (`/app/uploads`) responsável por hospedar anexos, radiografias e avatares inseridos pelos alunos.
- **`pdf_temp`**: Volume compartilhado entre o *Web App* e o *Celery Worker* para depósito e leitura de arquivos em trânsito.

---

## 4. Regras de Negócios Clínicas Importantes

### 4.1. Algoritmo de Diagnóstico Periodontal (AAP 2018)
O sistema não atua apenas como um repositório passivo. Ele contém um motor de diagnóstico interno codificado em Python. Quando o aluno preenche o periograma (Sangramento, Profundidade de Sondagem, Placa), o sistema varre as matrizes (JSON) em tempo real e calcula matematicamente o Estágio e Grau da Periodontite baseando-se estritamente na diretriz internacional da AAP 2018, emitindo o alerta clínico.

### 4.2. Tríplice Assinatura e Integração Contínua de Tratamento
Todo o processo clínico tem rastreabilidade garantida para a universidade:
1. O aluno gera o Plano de Tratamento.
2. O Professor aprova e aplica sua validação digital.
3. **Automação:** Ao aprovar, o sistema *importa automaticamente* o procedimento para a aba "Evolução Clínica", registrando as datas de forma precisa (utilizando instâncias `NOW()` no PostgreSQL).
4. O aluno preenche os aspectos técnicos na Evolução.
5. As assinaturas (Aluno Executor, Paciente via painel biométrico/Touch, e Validação Final do Professor) são criptografadas e armazenadas como string Base64 super leves no banco.

---

## 5. Questões Comuns e Manutenibilidade (Q&A de TI)

**P: Como atualizar o servidor e o código Python?**  
**R:** Em caso de refatorações ou modificações nos arquivos `.py`, o contêiner deve ser submetido a um "Rebuild". 
`docker compose build && docker compose up -d` 
Isso acontece pois o código fica congelado nativamente na imagem para garantir idoneidade na produção, não usando volumes *Live Reload*.

**P: Como é tratado o tráfego excessivo (DDoS/Spam)?**  
**R:** A aplicação conta com o módulo `Flask-Limiter` ligado nativamente ao Redis. Ataques de força bruta no Login, por exemplo, caem em quarentena recebendo erro `HTTP 429 - Too Many Requests`.

**P: O servidor vai encher o armazenamento rápido com imagens de Raio-X?**  
**R:** Negativo. A camada de *Services* intercepta qualquer upload de imagem no backend. Utilizando a biblioteca `Pillow`, as imagens brutas sofrem compressão de qualidade invisível antes da escrita em disco, preservando DPI (importante na odontologia) mas reduzindo tamanhos de 8MB para cerca de 400KB por foto.

**P: Onde configuro os acessos e senhas sensíveis?**  
**R:** Todo segredo (Chave JWT, Senhas do Banco, URL do Redis) fica blindado no arquivo `.env` na raiz do sistema host. Eles são passados para os contêineres unicamente em tempo de execução via variável de ambiente.

---
*Documentação gerada para suporte e avaliação de infraestrutura da instituição UMJ.*
