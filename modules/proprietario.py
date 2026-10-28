def pessoa_existe(conn, cpf):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM PESSOA
        WHERE CPF_CNPJ = :cpf
        """,
        {"cpf": cpf}
    )

    return cursor.fetchone() is not None

def cadastrar_supervisor(conn):
    print("\n--- Cadastro de Supervisor ---")

    print("\nInforme os seguintes dados:")

    cpf = input("CPF: ").strip()

    # Verifica se a pessoa já está cadastrada (pois uma mesma pessoa pode assumir vários papéis)
    if pessoa_existe(conn, cpf):
        print("\nPessoa já cadastrada. Reutilizando os dados já existentes...")

        registro_prof = input("Registro Profissional: ").strip()

        cadastrar_pessoa = False

    else:
        print("\nPessoa não cadastrada. Informe os demais dados.")

        nome = input("Nome: ").strip()
        telefone = input("Telefone: ").strip()
        email = input("Email: ").strip()
        senha = input("Senha: ").strip()
        registro_prof = input("Registro Profissional: ").strip()

        cadastrar_pessoa = True

    print('\nCadastrando...')

    cursor = conn.cursor()

    try:
        # Transação de escrita
        cursor.execute("SET TRANSACTION READ WRITE")
        
        if cadastrar_pessoa:
            # Inserção do novo supervisor na tabela genérica PESSOA
            cursor.execute(
                """
                INSERT INTO PESSOA
                (CPF_CNPJ, NOME, TELEFONE, EMAIL, SENHA)
                VALUES
                (:cpf, UPPER(:nome), :telefone, UPPER(:email), :senha)
                """,
                {
                    "cpf": cpf,
                    "nome": nome,
                    "telefone": telefone,
                    "email": email,
                    "senha": senha
                }
            )

        # Inserção do novo supervisor na tabela específica SUPERVISOR
        cursor.execute(
            """
            INSERT INTO SUPERVISOR
            (CPF_CNPJ, REGISTRO_PROFISSIONAL)
            VALUES
            (:cpf, :registro_prof)
            """,
            {
                "cpf": cpf,
                "registro_prof": registro_prof
            }
        )

        # Inserção da função dessa nova pessoa cadastrada (no caso supervisor)
        cursor.execute(
            """
            INSERT INTO FUNCAO
            (CPF_CNPJ, FUNCAO_PESSOA)
            VALUES
            (:cpf, 'SUPERVISOR')
            """,
            {
                "cpf": cpf
            }
        )

        conn.commit() # Salva as alterações
        print("\nSupervisor cadastrado com sucesso!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar supervisor: {e}")
        return False

def cadastrar_funcionario(conn):
    print("\n--- Cadastro de Funcionário ---")

    print("\nInforme os seguintes dados:")

    cpf = input("CPF: ").strip()

    if pessoa_existe(conn, cpf):
        print("\nPessoa já cadastrada. Reutilizando os dados já existentes...")

        cadastrar_pessoa = False

    else:
        print("\nPessoa não cadastrada. Informe os demais dados.")

        nome = input("Nome: ").strip()
        telefone = input("Telefone: ").strip()
        email = input("Email: ").strip()
        senha = input("Senha: ").strip()

        cadastrar_pessoa = True

    turno = input("Turno: ").strip()
    salario = input("Salario: ").strip()
    status = "TRABALHANDO" # Assume-se que novo funcionário estará com status TRABALHANDO
    # python-oracledb garante que se os valores forem None em Python serão enviados como NULL para o Oracle
    especialidade = None
    tipo = None
    qualificacao = None

    while True:
        print("\nEste funcionário será Agricultor?")
        print("1 - Sim")
        print("2 - Não")

        opcao = input("Selecione uma das opções: ").strip()

        if opcao == "1":
            eh_agricultor = "S"
            especialidade = input("Especialidade agrícola: ").strip()
            break

        elif opcao == "2":
            eh_agricultor = "N"
            break

        else:
            print("\nOpção inválida! Digite 1 ou 2.")

    while True:
        print("\nEste funcionário será Operador de Máquina?")
        print("1 - Sim")
        print("2 - Não")

        opcao = input("Selecione uma das opções: ").strip()

        if opcao == "1":
            eh_operador = "S"
            tipo = input("Tipo (ex: operador de colheitadeira): ").strip()
            qualificacao = input("Qualificação: ").strip()
            break

        elif opcao == "2":
            eh_operador = "N"
            break

        else:
            print("\nOpção inválida! Digite 1 ou 2.")

    print('\nCadastrando...')

    cursor = conn.cursor()

    try:
        # Transação de escrita
        cursor.execute("SET TRANSACTION READ WRITE")
        
        if cadastrar_pessoa:
            # Inserção do novo funcionário na tabela genérica PESSOA
            cursor.execute(
                """
                INSERT INTO PESSOA
                (CPF_CNPJ, NOME, TELEFONE, EMAIL, SENHA)
                VALUES
                (:cpf, UPPER(:nome), :telefone, UPPER(:email), :senha)
                """,
                {
                    "cpf": cpf,
                    "nome": nome,
                    "telefone": telefone,
                    "email": email,
                    "senha": senha
                }
            )

        # Inserção do novo funcionário na tabela específica FUNCIONARIO
        cursor.execute(
            """
            INSERT INTO FUNCIONARIO
            (
                CPF_CNPJ,
                DATA_ADMISSAO,
                TURNO,
                SALARIO,
                STATUS,
                EH_AGRICULTOR,
                ESPECIALIDADE_AGRICOLA,
                EH_OPERADOR,
                TIPO,
                QUALIFICACAO
            )
            VALUES
            (
                :cpf,
                SYSDATE,
                UPPER(:turno),
                :salario,
                :status,
                :eh_agricultor,
                UPPER(:especialidade),
                :eh_operador,
                UPPER(:tipo),
                UPPER(:qualificacao)
            )
            """,
            {
                "cpf": cpf,
                "turno": turno,
                "salario": salario,
                "status": status,
                "eh_agricultor": eh_agricultor,
                "especialidade": especialidade,
                "eh_operador": eh_operador,
                "tipo": tipo,
                "qualificacao": qualificacao,
            }
        )

        # Inserção da função dessa nova pessoa cadastrada (no caso funcionário)
        cursor.execute(
            """
            INSERT INTO FUNCAO
            (CPF_CNPJ, FUNCAO_PESSOA)
            VALUES
            (:cpf, 'FUNCIONARIO')
            """,
            {
                "cpf": cpf
            }
        )

        conn.commit() # Salva as alterações
        print("\nFuncionário cadastrado com sucesso!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar supervisor: {e}")
        return False

def menu(conn):
    while(True):
        print("\n--- Menu do Proprietário ---")
        print("1 - Cadastrar novo Supervisor")
        print("2 - Cadastrar novo Funcionário")
        print("0 - Voltar")

        opcao = int(input("\nEscolha uma opção para acessar: "))
        
        match opcao:
            case 1:
                cadastrar_supervisor(conn)
            case 2:
                cadastrar_funcionario(conn)
            case 0: 
                print("Redirecionando...")
                return
            case _: 
                print("Opção desconhecida.")