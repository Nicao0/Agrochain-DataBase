def cadastrar_atividade(conn):
    # Seria possível que o funcionário cadastra-se novas atividades realizadas em um lote,
    # registrando todas as informações acerca da atividade, como insumo utilizado, outros 
    # funcionários que a executaram, máquinas usadas e etc.
    None


def editar_atividade(conn):
    cursor = conn.cursor()

    cursor.execute(
        # Somente poderiam ser editadas atividades agrícolas que ainda não tivessem,
        # sido terminadas, ou até um prazo de 24hrs após seu término.
        # Protótipo, ideia:
        """
        SELECT *
        FROM ATIVIDADE_AGRICOLA A
        WHERE A.DATA_HORA_FIM IS NULL
        OR (SYSDATE - A.DATA_HORA_FIM) <= 1
        """
        # 1 (um dia)
    )

    ativs = cursor.fetchall()

    if not ativs:
        print("\nNenhuma atividade a ser editada.")
        return

    print("\n-> ATIVIDADES QUE PODEM SER EDITADAS")

def menu(conn):
    while(True):
        print("\n--- Menu do Funcionário ---")
        print("1 - Cadastrar Atividade Agrícola")
        print("2 - Editar Atividade Agrícola")
        print("0 - Voltar")

        opcao = int(input("\nEscolha uma opção para acessar: "))

        match opcao:
            case 1:
                # cadastrar_atividade(conn)
                print("Não implementado")
            case 2:
                # editar_atividade(conn)
                print("Não implementado")
            case 0: 
                print("Redirecionando...")
                return
            case _: 
                print("Opção desconhecida.")