# AgroChain: Rastreabilidade e Confiança de Ponta a Ponta

**Disciplina:** SCC0240 - Bases de Dados  
**Docente:** Profa. Dra. Elaine Parros Machado de Sousa  
**Instituição:** Instituto de Ciências Matemáticas e de Computação (ICMC) - Universidade de São Paulo (USP)  

O **AgroChain** é um sistema de banco de dados desenvolvido para registrar e disponibilizar o histórico completo de rastreabilidade da cadeia produtiva agrícola, com foco nas atividades relacionadas ao plantio. Alinhado aos princípios da Indústria 5.0, o projeto garante transparência nas operações rurais, monitoramento de insumos e responsabilidade socioambiental (como o descarte correto de agrotóxicos e emissão de CO2).

---

## 📖 Visão Geral

O sistema cobre todo o ciclo de produção, desde o preparo do lote até a colheita final. Ele registra operações, maquinários utilizados, funcionários envolvidos e insumos aplicados. 
Para garantir a confiança dos dados, as atividades agrícolas passam por um processo de validação técnica feita por supervisores. Por fim, as informações são disponibilizadas ao cliente final, permitindo que ele consulte o histórico da safra e saiba exatamente como o produto foi cultivado.

### ⚙️ Estrutura do Sistema (Entidades Principais)
* **Propriedade Rural & Lotes:** A unidade produtiva e suas subdivisões físicas.
* **Pessoa:** Funcionários, Supervisores, Proprietários e Clientes (modelo com sobreposição de papéis).
* **Insumos:** Controle de Agrotóxicos, Adubos e Fertilizantes.
* **Máquinas:** Registro de uso e consumo de diferentes combustíveis.
* **Atividade Agrícola & Validação:** O núcleo do sistema, relacionando o que foi feito no lote, quem fez, o que usou e a posterior aprovação do supervisor.
* **Safra:** O produto final disponibilizado para consulta do cliente.
* **Sustentabilidade:** Controle de Sensores IoT, emissão calculada de CO2 e rastreabilidade de Comprovantes de Descarte em Pontos de Coleta.

---

## 🛠️ Tecnologias e Implementação

* **SGBD:** Oracle Database.
* **Linguagem da Aplicação:** Python.
* **Bibliotecas Python:** `oracledb` (para conexão) e `python-dotenv` (para variáveis de ambiente).
* **Modelagem:** Modelo Entidade-Relacionamento (MER) convertido para Modelo Relacional completo com aplicação de formas normais.

A aplicação Python interage com o banco utilizando transações seguras (`READ ONLY`, `READ WRITE` e `SERIALIZABLE` para operações críticas) e consultas parametrizadas (bind variables) para prevenir SQL Injection.

---

## 🚀 Como Executar

### 1. Configuração do Banco de Dados
A pasta `sql/` contém todos os scripts necessários:
* Execute os scripts de criação (DDL) para gerar as tabelas no seu banco Oracle.
* Em seguida, rode os scripts de inserção (DML) disponibilizados para popular a base com os dados iniciais de teste.

### 2. Configuração da Aplicação Python
* Instale as dependências:
  ```bash
  python -m pip install oracledb python-dotenv
  ```
* Crie um arquivo `.env` na raiz do projeto com as credenciais do seu banco Oracle:
  ```env
  DB_USER=seu_usuario
  DB_PASSWORD=sua_senha
  DB_HOST=seu_host
  DB_PORT=sua_porta
  DB_SERVICE=seu_service
  ```

### 3. Uso do Sistema
Execute o script principal (ex: `main.py`) para abrir o menu do sistema.
* **Usuário de Teste (Admin Geral):** Login: `JOAO@EMAIL.COM` | Senha: `SENHA123` (Possui privilégios de Proprietário, Supervisor e Funcionário).
* **Usuário de Teste (Cliente):** Login: `ALEX@EMAIL.COM` | Senha: `SENHA999` (Acesso às consultas da cadeia produtiva e emissões).

---
*Para detalhes profundos sobre as escolhas de mapeamento relacional, queries complexas (divisão relacional, agregações LISTAGG), tratamento de ciclos e transações, consulte o documento PDF completo fornecido junto ao projeto.*
