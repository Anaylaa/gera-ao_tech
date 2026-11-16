# 📚 LibraTech — Sistema de Gerenciamento de Biblioteca

Sistema web para gerenciamento de uma biblioteca universitária, desenvolvido com **Python, FastAPI, PostgreSQL e JavaScript**, utilizando Docker para facilitar a configuração e execução do ambiente.

O LibraTech permite organizar o acervo bibliográfico, cadastrar leitores, controlar empréstimos e devoluções, gerenciar renovações e acompanhar multas.

---

## 🎯 Objetivo do projeto

Desenvolver uma aplicação web para automatizar as principais operações de uma biblioteca universitária, garantindo controle do acervo, organização dos empréstimos e aplicação consistente das regras de negócio.

O projeto também tem como objetivo aplicar conceitos de desenvolvimento backend, APIs REST, bancos de dados relacionais, arquitetura em camadas, testes automatizados e conteinerização.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python 3.12 | Linguagem principal do backend |
| FastAPI | Construção da API REST |
| Uvicorn | Servidor ASGI |
| SQLAlchemy | ORM e persistência de dados |
| PostgreSQL 16 | Banco de dados relacional |
| Pydantic | Validação e estruturação dos dados |
| Alembic | Controle de migrações do banco |
| HTML5 | Estrutura do frontend |
| CSS3 | Estilização e responsividade |
| JavaScript | Interatividade e integração com a API |
| Docker | Conteinerização da aplicação |
| Docker Compose | Orquestração dos serviços |
| Pytest | Testes automatizados |
| Ruff | Análise estática e padronização do código |

## ✨ Funcionalidades

### Dashboard
- Resumo da quantidade de livros cadastrados.
- Quantidade de leitores.
- Empréstimos ativos.
- Multas pendentes.
- Empréstimos recentes.
- Acompanhamento de prazos de devolução.

### Acervo
- Cadastro de livros.
- Consulta dos livros cadastrados.
- Identificação por título, autor, ISBN e categoria.
- Controle de quantidade total e disponível.
- Pesquisa e filtragem por categoria.

### Leitores
- Cadastro de leitores.
- Consulta dos leitores registrados.
- Armazenamento de nome, e-mail e telefone.
- Pesquisa por nome ou e-mail.

### Empréstimos
- Registro de empréstimos.
- Associação entre livros e leitores.
- Controle de datas.
- Consulta dos empréstimos.
- Identificação da situação dos empréstimos.

### Devoluções
- Registro de devoluções.
- Atualização do estoque disponível.
- Cálculo de multas por atraso.

### Renovações
- Renovação de empréstimos dentro das regras estabelecidas.
- Controle da quantidade de renovações.
- Atualização da data prevista de devolução.

### Multas
- Identificação de multas pendentes.
- Consulta dos valores.
- Registro de pagamentos.
- Controle da situação do pagamento.

### Relatórios
- Quantidade de livros disponíveis.
- Quantidade de livros emprestados.
- Empréstimos atrasados.
- Taxa de ocupação do acervo.
- Distribuição de livros por categoria.
- Exportação de relatórios em CSV.

## 📋 Regras de negócio

As regras abaixo definem o funcionamento do sistema.

| Regra | Descrição |
|---|---|
| Prazo de empréstimo | 30 dias corridos |
| Limite de empréstimos | Até 10 empréstimos ativos por leitor |
| Limite de renovações | Até 5 renovações por empréstimo |
| Prazo de renovação | Cada renovação acrescenta 30 dias à data prevista atual |
| Renovação em atraso | Empréstimos atrasados não podem ser renovados |
| Multa | R$ 1,00 por dia de atraso, por exemplar |
| Bloqueio de leitor | Leitores com empréstimos atrasados não podem realizar novos empréstimos |
| Controle de estoque | O estoque disponível diminui no empréstimo e aumenta na devolução |
| ISBN | Não deve existir duplicidade de ISBN |
| E-mail | Não deve existir duplicidade de e-mail entre leitores |

## 🏗️ Arquitetura do projeto

O backend foi organizado em camadas para separar responsabilidades e facilitar a manutenção.

```text
LibraTech/
│
├── app/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repositories.py
│   │   └── services.py
│   │
│   ├── frontend/
│   │   ├── index.html
│   │   ├── style.css
│   │   ├── script.js
│   │   └── assets/
│   │
│   ├── tests/
│   │
│   ├── migrations/
│   │
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── compose.prod.yaml
│
├── .env.example
├── .gitignore
└── README.md
```

### Responsabilidades das camadas

**main.py**
- Inicialização da aplicação FastAPI.
- Definição das rotas HTTP.
- Recebimento das requisições.
- Retorno das respostas e dos códigos HTTP.

**models.py**
- Definição das entidades e tabelas do banco de dados por meio do SQLAlchemy.

**schemas.py**
- Validação dos dados de entrada.
- Estruturação dos dados de saída.
- Definição dos contratos da API.

**repositories.py**
- Acesso e operações de persistência no banco de dados.

**services.py**
- Implementação das regras de negócio.
- Validação das operações.
- Orquestração dos processos de empréstimo, devolução, renovação e multas.

**database.py**
- Configuração da conexão com o banco.
- Gerenciamento das sessões do SQLAlchemy.

**migrations/**
- Histórico e controle das alterações do banco de dados por meio do Alembic.

**frontend/**
- Interface de gerenciamento da biblioteca.
- Comunicação com a API.
- Exibição dos dados e interação com o usuário.

**tests/**
- Testes automatizados das funcionalidades e regras de negócio.

## 🔌 API REST

A API disponibiliza documentação interativa pelo Swagger.

Após iniciar a aplicação, acesse:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Principais rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Página inicial |
| GET | `/health` | Verificação da API |
| GET | `/health/db` | Verificação da conexão com o banco |
| POST | `/livros` | Cadastro de livro |
| GET | `/livros` | Listagem de livros |
| GET | `/livros/{livro_id}` | Consulta de livro |
| POST | `/leitores` | Cadastro de leitor |
| GET | `/leitores` | Listagem de leitores |
| GET | `/leitores/{leitor_id}` | Consulta de leitor |
| POST | `/emprestimos` | Registro de empréstimo |
| GET | `/emprestimos` | Listagem de empréstimos |
| GET | `/emprestimos/{emprestimo_id}` | Consulta de empréstimo |
| POST | `/emprestimos/{emprestimo_id}/devolucao` | Registro de devolução |
| POST | `/emprestimos/{emprestimo_id}/renovacao` | Renovação de empréstimo |
| POST | `/emprestimos/{emprestimo_id}/pagamento-multa` | Registro de pagamento de multa |

Os contratos completos de requisição e resposta podem ser consultados no Swagger.

## 🚀 Como executar o projeto

### Pré-requisitos

- Git.
- Docker Desktop.
- Docker Compose.
- Navegador web.

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd NOME_DO_REPOSITORIO
```

### 2. Configurar as variáveis de ambiente

Crie seu arquivo `.env` com base no modelo fornecido:

```bash
cp .env.example .env
```

No Windows PowerShell, também é possível utilizar:

```powershell
Copy-Item .env.example .env
```

Preencha as variáveis necessárias conforme o modelo do projeto. Não compartilhe seu arquivo `.env`.

### 3. Construir e iniciar os containers

```bash
docker compose up --build -d
```

### 4. Verificar os containers

```bash
docker compose ps
```

Aguarde o banco de dados ficar saudável e a API iniciar.

### 5. Acessar a aplicação

Frontend:

`http://localhost:8000/`

Documentação:

`http://localhost:8000/docs`

### 6. Consultar os logs

```bash
docker compose logs -f api
```

Para consultar os logs do banco:

```bash
docker compose logs -f db
```

### 7. Encerrar os serviços

```bash
docker compose down
```

O comando acima encerra os containers sem remover o volume persistente do banco de dados.

## 🧪 Testes e qualidade de código

O projeto utiliza Pytest para validar o comportamento da aplicação.

### Executar os testes

```bash
docker compose exec api python -m pytest -q -p no:cacheprovider
```

### Executar o Ruff

```bash
docker compose exec api sh -c 'ruff check --no-cache --cache-dir /tmp/ruff-cache $(find app tests migrations -type f -name "*.py")'
```

### Resultado da última execução registrada

- 72 testes aprovados.
- Análise estática do Ruff aprovada.
- Cobertura de testes anteriormente registrada em 100% para os módulos avaliados.

A suíte automatizada utiliza SQLite. Os testes integrados específicos do PostgreSQL e a validação manual de todos os cenários de negócio devem ser considerados separadamente.

## 🔍 Validação funcional

Além dos testes automatizados, recomenda-se validar:

- Cadastro e consulta de livros.
- Cadastro e consulta de leitores.
- Empréstimos e atualização de estoque.
- Devoluções.
- Limite de empréstimos por leitor.
- Limite de renovações.
- Bloqueio de leitores com atraso.
- Cálculo e pagamento de multas.
- Persistência dos dados após reinicialização.
- Funcionamento integrado com PostgreSQL.
- Pesquisa, filtros, relatórios e exportação CSV.

## 🔐 Segurança e boas práticas

- Não versionar arquivos `.env`.
- Não publicar senhas ou credenciais.
- Não compartilhar dados pessoais reais nos testes.
- Utilizar validação de dados na API.
- Manter as regras de negócio concentradas na camada de serviços.
- Preservar a integridade do banco de dados.
- Utilizar as migrations para controlar alterações estruturais.

## 👥 Desenvolvimento em equipe

O projeto foi estruturado para permitir que diferentes integrantes possam colaborar no desenvolvimento e na validação das funcionalidades.

Sugestão de fluxo de colaboração:

1. Clonar o repositório.
2. Criar uma branch para cada atividade.
3. Executar o projeto localmente.
4. Validar as funcionalidades.
5. Registrar problemas encontrados como Issues.
6. Enviar alterações por Pull Requests.


**LibraTech — Sistema de Gerenciamento de Biblioteca**

Projeto acadêmico desenvolvido para aplicar conceitos de desenvolvimento web, engenharia de software, APIs REST, bancos de dados relacionais, testes automatizados e conteinerização.
