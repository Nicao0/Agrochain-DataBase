from db_connect import get_connection
import modules.cliente as cliente
import modules.funcionario as funcionario
import modules.proprietario as proprietario
import modules.supervisor as supervisor

# A prevenção contra SQL Injection foi feita usando consultas parametrizadas,
# evitando concatenações maliciosas às consultas (como (' OR 1=1 --))

def validar_usuario(conn, email, senha):
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            """
            SELECT CPF_CNPJ, NOME
            FROM PESSOA
            WHERE EMAIL = :email
              AND SENHA = :senha
            """,
            {
                "email": email,
                "senha": senha
            }
        )

        usuario = cursor.fetchone()

        conn.commit() # Encerra a transação
        return usuario

    except Exception as e:
        conn.rollback()
        print(f"Erro ao validar usuário: {e}")
        return None


def cadastrar_cliente(conn, cpf, nome, telefone, email, senha):
    cursor = conn.cursor()

    # Inserção do novo cliente na tabela genérica PESSOA
    try:
        cursor.execute("SET TRANSACTION READ WRITE")

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

        # Inserção do novo cliente na tabela específica CLIENTE
        cursor.execute(
            """
            INSERT INTO CLIENTE
            (CPF_CNPJ, DATA_CADASTRO)
            VALUES
            (:cpf, SYSDATE)
            """,
            {
                "cpf": cpf
            }
        )

        # Inserção da função dessa nova pessoa cadastrada (no caso cliente)
        cursor.execute(
            """
            INSERT INTO FUNCAO
            (CPF_CNPJ, FUNCAO_PESSOA)
            VALUES
            (:cpf, 'CLIENTE')
            """,
            {
                "cpf": cpf
            }
        )

        conn.commit()  # Salva as alterações e encerra transação
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar cliente: {e}")
        return False


def obter_funcoes(conn, cpf_cnpj):
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            """
            SELECT FUNCAO_PESSOA
            FROM FUNCAO
            WHERE CPF_CNPJ = :cpf
            ORDER BY FUNCAO_PESSOA
            """,
            {
                "cpf": cpf_cnpj
            }
        )

        funcoes = [linha[0] for linha in cursor.fetchall()]

        conn.commit() # Encerra a transação
        return funcoes

    except Exception as e:
        conn.rollback()
        print(f"Erro ao obter funções: {e}")
        return []


def escolher_funcao(funcoes):
    print("\n--- Suas Funções ---")

    for i, funcao in enumerate(funcoes, start=1):
        print(f"{i} - {funcao}")

    while True:
        try:
            opcao = int(input("\nEscolha a função para acessar: "))

            if 1 <= opcao <= len(funcoes):
                return funcoes[opcao - 1]

            print("Opção inválida.")

        except ValueError:
            print("Digite um número válido.")


def redirecionar(conn, funcao, cpf_cnpj):
    if funcao == "CLIENTE":
        cliente.menu(conn, cpf_cnpj)

    elif funcao == "PROPRIETARIO":
        proprietario.menu(conn)

    elif funcao == "SUPERVISOR":
        supervisor.menu(conn, cpf_cnpj)

    elif funcao == "FUNCIONARIO":
        funcionario.menu(conn)

    else:
        print("Função não reconhecida.")

def sessao(conn, cpf_cnpj):
    while True:
        funcoes = obter_funcoes(conn, cpf_cnpj)

        if len(funcoes) == 1:
            funcao = funcoes[0]
        else:
            funcao = escolher_funcao(funcoes)

        redirecionar(conn, funcao, cpf_cnpj)

        print("\n1 - Continuar logado")
        print("0 - Logout")

        opcao = input("Escolha: ")

        if opcao == "0":
            break

def login(conn):
    email = input("Email: ").strip()
    senha = input("Senha: ").strip()

    usuario = validar_usuario(conn, email, senha)

    if usuario is None:
        print("Email ou senha inválidos.")
        return

    cpf_cnpj, nome = usuario

    print(f"\nBem-vindo(a), {nome}!")

    sessao(conn, cpf_cnpj)


def cadastro(conn):
    print("\n--- Cadastro de Cliente ---")

    print("\nInforme os seguintes dados:")

    cpf = input("CPF: ").strip()
    nome = input("Nome: ").strip()
    telefone = input("Telefone: ").strip()
    email = input("Email: ").strip()
    senha = input("Senha: ").strip()

    print('\nCadastrando...')

    if cadastrar_cliente(
        conn,
        cpf,
        nome,
        telefone,
        email,
        senha
    ):
        print("Cliente cadastrado com sucesso!\n")

        sessao(conn, cpf)

def main():
    conn = get_connection()

    if conn is None:
        print("Erro ao conectar ao banco.")
        return

    try:
        print("\n=== AGROCHAIN ===")
        print("1 - Entrar")
        print("2 - Cadastrar-se como Cliente")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            login(conn)

        elif opcao == "2":
            cadastro(conn)

        else:
            print("Opção inválida.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()