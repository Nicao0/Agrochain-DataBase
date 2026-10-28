def avaliar_atividade(conn, cpf_supervisor):
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            """
            SELECT ID_ATIVIDADE, TIPO_ATIVIDADE, DATA_HORA_INICIO, DATA_HORA_FIM
            FROM ATIVIDADE_AGRICOLA A
            WHERE A.DATA_HORA_FIM IS NOT NULL
            AND NOT EXISTS (
                SELECT 1
                FROM VALIDACAO V
                WHERE V.ID_ATIVIDADE = A.ID_ATIVIDADE
            )
            ORDER BY ID_ATIVIDADE
            """
        )

        atividades = cursor.fetchall()

        conn.commit()

        if not atividades:
            print("\nNenhuma atividade sem avaliação.")
            return

        print("\n--- ATIVIDADES A SEREM AVALIADAS ---")

        for atividade in atividades:
            print(f"- ID: {atividade[0]} -")
            print(f"Tipo: {atividade[1]}")
            print(f"Início: {atividade[2]}")
            print(f"Fim: {atividade[3]}")
            print()

        ids_validos = {a[0] for a in atividades}

        while True:
            try:
                id_atividade = int(input("Digite o ID da atividade: "))

                if id_atividade in ids_validos:
                    break
                else:
                    print("ID inválido! Escolha apenas atividades listadas.")

            except ValueError:
                print("Digite apenas números válidos.")

        opcao = input("\nAvalie:\n1 - APROVADA\n2 - REJEITADA\nEscolha: ")

        if opcao == "1":
            status = "APROVADO"
        elif opcao == "2":
            status = "REJEITADO"
        else:
            print("Opção inválida.")
            return

        try:
            # Para evitar que dois supervisores tentem cadastrar avaliação para a mesma atividade,
            # ao menos tempo, evitando um estado de inconsistencia, pois há somente uma avaliação
            # para cada atividade, foi utilizada transação SERIALIZABLE
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

            cursor.execute(
                """
                INSERT INTO VALIDACAO
                (ID_ATIVIDADE, CPF_CNPJ_SUPERVISOR, DATA_HORA, STATUS)
                VALUES (:1, :2, SYSDATE, :3)
                """,
                (id_atividade, cpf_supervisor, status)
            )

            conn.commit()
            print("\nValidação registrada com sucesso!")

        except Exception as e:
            conn.rollback()
            print("Erro ao registrar validação:", e)

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")

def atividades_validadas(conn):
    cursor = conn.cursor()

    try:
        # Transação somente de leitura
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            """
            SELECT
                A.ID_ATIVIDADE,
                A.TIPO_ATIVIDADE,
                A.DATA_HORA_INICIO,
                A.DATA_HORA_FIM,
                P.NOME,
                V.STATUS,
                V.DATA_HORA
            FROM ATIVIDADE_AGRICOLA A

            JOIN VALIDACAO V
                ON V.ID_ATIVIDADE = A.ID_ATIVIDADE

            JOIN PESSOA P
                ON P.CPF_CNPJ = V.CPF_CNPJ_SUPERVISOR

            ORDER BY A.ID_ATIVIDADE
            """
        )

        ativs = cursor.fetchall()

        if not ativs:
            print("\nNenhuma atividade avaliada ainda.")
            conn.commit()
            return

        print("\n-> ATIVIDADES VALIDADAS")

        for a in ativs:
            print(f"\n- ID: {a[0]} - ")
            print(f"Tipo: {a[1]}")
            print(f"Início: {a[2]}")
            print(f"Fim: {a[3]}")
            print(f"Supervisor: {a[4]}")
            print(f"Status: {a[5]}")
            print(f"Data da avaliação: {a[6]}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Erro:", e)

def menu(conn, cpf_cnpj):
    while(True):
        print("\n--- Menu do Supervisor ---")
        print("1 - Avaliar Atividade Agrícola")
        print("2 - Consultar Atividades Agrícolas já validadas")
        print("0 - Voltar")

        opcao = int(input("\nEscolha uma opção para acessar: "))
        
        match opcao:
            case 1:
                avaliar_atividade(conn, cpf_cnpj)
            case 2:
                atividades_validadas(conn)
            case 0: 
                print("Redirecionando...")
                return
            case _: 
                print("Opção desconhecida.")