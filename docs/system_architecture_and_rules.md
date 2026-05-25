# Documentação de Arquitetura e Engenharia: Gestão Clínica Odontológica (UMJ)

Este documento centraliza as diretrizes arquiteturais, a mecânica da base de dados e os principais motores lógicos em execução no sistema. Ele é um guia definitivo para desenvolvedores e IAs assumirem a manutenção, o debug e a expansão responsável da aplicação.

---

## 1. Visão Geral da Arquitetura e Stack

A aplicação foi desenhada de forma monolítica, priorizando a estabilidade, a ausência de gargalos complexos de build e o fácil deployment em servidores tradicionais (ou Nginx reverso).

*   **Linguagem Core:** Python 3.
*   **Web Framework:** Flask 3.0.3 rodando sobre Gunicorn/Gevent (WSGI). A entrada primária é estruturada no `app.py` que implementa *ProxyFix* para lidar de forma nativa com proxies reversos do Nginx.
*   **Banco de Dados:** PostgreSQL via `psycopg2` e pool `ThreadedConnectionPool`. **IMPORTANTE: Não há uso de ORMs (como SQLAlchemy).** Todas as consultas são escritas em RAW SQL através de scripts empacotadores definidos em `database.py`.
*   **Cache, Sessões e Filas:** Redis é usado para cache, sessões server-side, broker/backend do Celery e apoio ao rate limiting.
*   **Front-End:** Renderização _Server-Side_ (SSR) com **Jinja2**. Elementos interativos (Modais, Signatures de Canvas, Tabs) utilizam **Vanila JavaScript**.
*   **Estilização:** CSS3 puro, fundamentado fortemente em variáveis nativas HSL (Hue, Saturation, Lightness) localizadas no root (`:root`), permitindo sub-temas nativos sem dependência pesada de frameworks (como Bootstrap ou Tailwind).
*   **Autenticação e Segurança:** Gerenciado pelo `flask_login` aliada ao `Flask-WTF` para proteção pervasiva de CSRF.
*   **Geração Legal de Documentos:** Uso da biblioteca `WeasyPrint` para transcrição de rotas HTML para binários de PDF (tamanho A4) de alta fidelidade visual (receitas, atestados, etc).

---

## 2. Padrões de Banco de Dados (`database.py`)

A interação com banco de dados baseia-se em cursores `RealDictCursor`, garantindo retorno semelhante a dicionários para leitura de dados (`row['campo']`). A aplicação usa PostgreSQL de forma direta, sem ORM.

### 2.1. Funções Core
*   `query(sql, params, one=False)`: Utilizada para extração (SELECT). O parâmetro `one=True` retorna uma linha solitária em vez de um array.
*   `execute(sql, params)`: Utilizada para mutações (INSERT, UPDATE, DELETE). Quando a consulta usa `RETURNING id`, retorna o ID criado/afetado.
*   `execute_returning(sql, params)`: Atalho para `INSERT` com `RETURNING id`.
*   `execute_transaction(statements)`: Executa uma lista de comandos em transação atômica.

### 2.2. Placeholders PostgreSQL
Todas as queries parametrizadas devem usar placeholders do `psycopg2`: `%s`.
```python
query("SELECT id FROM users WHERE username = %s", (username,), one=True)
execute(
    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
    (username, hashed_password, role),
)
```
O placeholder antigo do SQLite (`?`) nao deve ser usado no codigo ativo.

### 2.3. Mutação de Linhas para Jinja
As linhas retornadas pelo `RealDictCursor` já se comportam como dicionários. Ainda assim, quando uma rotina precisar enriquecer registros para o Jinja, prefira converter explicitamente para `dict` antes de injetar chaves virtuais. Isso mantém o código tolerante a mudanças futuras no tipo de cursor.
> ```python
> raw_rows = query("SELECT ...")
> formated_rows = [dict(r) for r in raw_rows]
> formated_rows[0]['novo_campo'] = 'valor_injetado'
> ```

### 2.4. Datas Vindas do PostgreSQL
Campos temporais (`TIMESTAMP`, `DATE`) podem chegar ao Jinja como objetos Python (`datetime.datetime`/`date`), nao como strings. Evite `split`, slicing ou operadores de string diretamente sobre esses valores.
```jinja2
{{ (paciente.criado_em|string).split(' ')[0] }}
```

### 2.5. NoSQL Dinâmico inserido no SQL
Para recursos que se manifestam como matrizes transientes (ex: uma lista de 5 remédios ou matriz de um Odontograma de 32 dentes colorido), evitou-se propositalmente criar arquiteturas super normalizadas (Tabelas Relacionais 1:N maciças).
*   **Mecânica:** Os campos são marcados como `TEXT` no banco. Ferramentas `json.dumps()` e `json.loads()` embutem ou interpretam matrizes de dicionários sob a demanda, provendo agilidade e elasticidade nas consultas dinâmicas frente ao Front-End. O template HTML usa nomes de arrays, como `name="campo[]"`, resolvidos via `request.form.getlist('campo[]')`.

---

## 3. Topologia dos Módulos (Blueprints)

O sistema emprega *Blueprints* independentes atreladas a roteamentos e fluxos singulares de vida.

1.  **`auth.py` e `admin.py` (Controle e Perfis):** Lidam com a gestão de RBAC (Role-Based Access Control). Os níveis de hierarquia ativa limitam a navegação e a autoria:
    *   `admin`: Controle absoluto (cadastros e remoções no painel).
    *   `professor`: Único autorizador clínico capacitado para dar despachos ou fechar laudos vinculativos.
    *   `aluno`: Ator logístico operacional de inserção clínica, barrado em encerramentos.
    *   `atendimento` (Secretaria): Acesso parcial de edição cadastral mas sem acesso profundo para apagar histórico restrito.
2.  **`patients.py` (O Cérebro do Sistema):** Aciona a mega-rota `/view/<id>`. Emulando quase uma "SPA", ela resgata todos os *joins* de históricos do paciente e bombeia para o motor do Jinja popularizar todas as marcações passadas simultaneamente em dezenas de *"Tabs"*.
3.  **`exams.py`:** Abriga o motor lógico de sub-exames (Físico, Placa, Odontograma e Periograma), isolando pesados dados do paciente.
4.  **`prosthesis.py`:** Organiza o fluxo temporal de tratamentos reabilitadores (PPR/Total). Segrega as áreas de controle financeiro (valores cobrados, abates) e "etapas em laboratório".
5.  **`documents.py`:** Responsável exclusivo pelos controladores de exportação e impressão (Weasyprint) acionados a nível judicial e de laboratório.

---

## 4. Motores Lógicos e Regras de Negócio Cruciais

### 4.1. Bloqueio Obrigatório de TCLE
Pilar bioético e clínico. Nenhum aluno ou professor pode iniciar a triagem e o tratamento se a tabela virtual `patient_tcle` atrelada àquele paciente específico estiver morta.
*   **O Gatilho:** A carga da `/view/<id>` varre a busca. Na frente HTML, 99% das paletas e funções são removidas do DOM caso exista falha na chancela do termo de consentimento (que exige a placa via `signature_pad` - assinatura base64 real).

### 4.2. Autorização de Nível de Professor (Trancamento de Laudo)
Todas as operações de peso pericial, notadamente Diagnósticos e Fechamentos de Fases Reabilitadoras não adquirem status definitivo automaticamente.
*   Elas são gravadas inicialmente como rascunhos assíncronos (geralmente identificados pelo gatilho HTML e no Banco).
    *   Um botão exclusivo chamado **"Validar"** aparece unicamente para `professores`/`admin`. Clicar aciona o duplo fator do Modal; o professor insere a senha criptografada em *hash*. Sendo bem-sucedido, o timestamp de `data_validacao` dita o status, bloqueando edições no POST para aquele ID perpetuamente.

### 4.3. Regras do Plano de Tratamento e Evolução Clínica (Atendimento)
Fluxo automatizado para garantir integridade e agilidade:
1.  **Plano de Tratamento:** A numeração das sessões é sequencial (1, 2, 3...) baseada na ordem de criação (`criado_em`), eliminando a necessidade de inserção manual de data nesta fase. O campo "Dente" é opcional.
2.  **Importação Automática:** Assim que um `professor` assina um procedimento no Plano de Tratamento, ele é automaticamente importado para a aba **Atendimento (Evolução Clínica)** com status 'Concluido'.
3.  **Tríplice Assinatura (Evolução):** Para que a execução seja validada legalmente na Evolução, são necessárias 3 assinaturas:
    *   **Aluno Executor:** Confirma a realização do procedimento via login/senha.
    *   **Paciente:** Assinatura biométrica/digital via `signature_pad`.
    *   **Professor:** Valida a execução final via login/senha.
4.  **Geração Automática de Data:** A data (`timestamp`) do atendimento só é gerada e gravada no banco quando a **última** das 3 assinaturas é capturada. Registros manuais de atendimento pulam este gatilho e permitem data manual.

### 4.4. Motor de Inspeção e Diagnóstico Periodontal IA (AAP 2018)
O módulo (`exam_periograma` em `exams.py`) abriga o motor funcional que gera a condição clínica (Diagnóstico Automático da Nova Classificação 2018):
1.  **Estrutura de Dados:** O front-end envia um JSON hierárquico encapsulando sítios interproximais e dados do dente como um todo (Mobilidade, Implante, Furca). Ex: `{"18": {"mobilidade": 2, "furca": 0, "sitios": {...}}}`.
2.  **Gatilho de Doença:** A IA acusa Periodontite se houver QUALQUER sítio interproximal com PIC >= 1mm, ou se os modificadores de complexidade extremos estiverem presentes. A regra antiga de "adjacência anatômica" foi removida.
3.  **Estadiamento (Severidade e Complexidade):** O Estágio base (I a IV) é ditado pelo pior PIC interproximal da boca. Este estágio pode sofrer "upgrade" (nunca downgrade) pelos modificadores de complexidade (Profundidade de Sondagem >= 5mm, Envolvimento de Furca Grau II/III, Mobilidade Grau II/III). 
4.  **Extensão:** Calculada rigorosamente pela porcentagem de dentes presentes afetados (Localizada < 30% vs Generalizada >= 30%).
5.  **Grau (Progressão):** Uma função isolada aciona Regex (`determinar_grau_periodontal`) no texto de Anamnese. Pacientes com diabetes descompensada ou alto tabagismo escalam ao Grau C. O padrão é Grau B, e pacientes expressamente saudáveis reduzem ao Grau A.

### 4.5. A Arquitetura Limitante de Impressão (WeasyPrint) vs Client-Side (html2pdf)
Os artefatos servidos pela engine interna convertem o CSS submisso usando as linguagens clássicas e duras, bloqueando novidades do CSS3 (exemplo Flexbox avançado).
*   **A Regra da Solidez:** Todo novo PDF gerado pelas atualizações em `templates/pdfs` DEVE utilizar `display: table`, recuos rígidos `margin/padding`, fontes explícitas seguras do sistema (Arial, Helvetica) e rejeitar web-fonts longas, com objetivo de impedir a inversão ou falha de leitura em hardwares de impressão física da clínica.
*   **A Exceção Periograma (Client-Side):** Devido à complexa renderização visual de CSS Sprites com sobreposição de sangramentos no DOM, o Periograma **não usa o WeasyPrint**. Ele implementa o `html2pdf.js` diretamente na view, capturando a renderização matricial do layout de sprites dinâmicos de 16x2 (`dental_teeth_v3.png`) e convertendo para PDF paisagem (A4) na máquina do usuário localmente.

---

## 5. Práticas Futuras a IAs e Engenheiros
1.  **Migrações:** Como não existe arquitetura de migração automática como o `Alembic`, se introduzir um campo no `database.py` novo (ex: adicionando `foto` à tabela usuário), registre a coluna na estrutura de criação e em blocos compatíveis com PostgreSQL usando `information_schema`/`ALTER TABLE`. A função `_ensure_columns_exist` é o padrão local para evitar falha na subida quando a tabela já existe.
2.  **Mutações Ocultas JS:** Fique atento aos comportamentos assíncronos. Exemplo explícito do Odontograma onde o Javascript pinta a superfície de uma face, salva as strings das cores em um dicionário invisível escondido que trafega nos Inputs para cruzar via Formulário.

— _Documentação consolidada durante a arquitetura final da engine da Clínica (UMJ)._
