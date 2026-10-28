def consultar_propriedade(conn):
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            # Só haverá uma tupla em propriedade rural, pois nosso sistema foi projetado
            # para atender apenas à uma propriedade rural com todo o seu processo produtivo
            """
            SELECT *
            FROM PROPRIEDADE_RURAL
            """
        )

        propriedade = cursor.fetchone()

        if propriedade is None:
            print("Nenhuma propriedade cadastrada.")
            return

        print("\n-> INFORMAÇÕES")
        print(f"Código do Imóvel: {propriedade[0]}")
        print(f"Nome: {propriedade[1]}")
        print(f"CEP: {propriedade[2]}")
        print(f"Número: {propriedade[3]}")
        print(f"Logradouro: {propriedade[4]}")
        print(f"Cidade: {propriedade[5]}")
        print(f"Estado: {propriedade[6]}")
        print(f"País: {propriedade[7]}")
        print(f"Área Total: {propriedade[8]} ha\n")

        conn.commit() # Encerra a transação
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")

def exibir_safras_disponiveis(conn, cpf_cliente):
    cursor = conn.cursor()

    try:
        cursor.execute("SET TRANSACTION READ WRITE")
        cursor.execute(
            """
            SELECT ID_SAFRA, NUM_LOTE, DATA_HORA_PLANTIO, DATA_HORA_COLHEITA, QUANTIDADE
            FROM SAFRA
            WHERE DATA_HORA_COLHEITA IS NOT NULL
            AND QUANTIDADE > 0
            """
            # Safras com quantidade 0 são consideradas vendidas, por isso não aparecem
            # como opção de consulta
        )

        safras = cursor.fetchall()

        if not safras:
            print("\nNenhuma safra disponível.")
            return

        print("\n-> SAFRAS DISPONÍVEIS")

        for safra in safras:
            print(f"\n- Safra de ID: {safra[0]} -")
            print(f"Lote: {safra[1]}")
            print(f"Plantio: {safra[2]}")
            print(f"Colheita: {safra[3]}")
            print(f"Quantidade: {safra[4]}")
        print()

        # Evita tentar acessar Safras ainda não disponíveis
        ids_validos = {safra[0] for safra in safras}

        while True:
            try:
                safra_id = int(input("\nInforme o ID da Safra que deseja consultar: "))

                if safra_id in ids_validos:
                    break
                else:
                    print("ID inválido! Escolha apenas uma das safras listadas.")

            except ValueError:
                print("Digite apenas números válidos.")
        
        # Consulta a Safra selecionada
        cursor.execute(
                """
                SELECT
                    A.ID_ATIVIDADE,
                    A.TIPO_ATIVIDADE,
                    A.DATA_HORA_INICIO,
                    A.DATA_HORA_FIM,
                    A.DURACAO,
                    A.AREA_TRABALHADA,
                    A.TEMPO_USO_MAQUINAS,
                    A.EMISSAO_CO2,

                    I.COD_BARRAS,
                    I.NOME AS NOME_INSUMO,
                    I.TIPO AS TIPO_INSUMO,

                    LISTAGG(DISTINCT P.NOME, ', ') 
                        WITHIN GROUP (ORDER BY P.NOME) AS FUNCIONARIOS,

                    LISTAGG(
                        DISTINCT M.NUMERO_SERIE || ' - ' || M.MODELO || ' (' || M.COMBUSTIVEL_EM_USO || ')',
                        ' | '
                    ) WITHIN GROUP (ORDER BY M.NUMERO_SERIE) AS MAQUINAS

                FROM SAFRA S

                JOIN ATIVIDADE_AGRICOLA A
                    ON A.COD_IMOVEL_RURAL = S.COD_IMOVEL_RURAL
                    AND A.NUM_LOTE = S.NUM_LOTE

                LEFT JOIN INSUMO I
                    ON I.COD_BARRAS = A.COD_BARRAS_INSUMO

                JOIN REALIZADA_POR R
                    ON R.ID_ATIVIDADE = A.ID_ATIVIDADE

                JOIN FUNCIONARIO F
                    ON F.CPF_CNPJ = R.CPF_CNPJ_FUNC

                JOIN PESSOA P
                    ON P.CPF_CNPJ = F.CPF_CNPJ

                LEFT JOIN OPERA O
                    ON O.ID_ATIVIDADE = A.ID_ATIVIDADE

                LEFT JOIN MAQUINA M
                    ON M.NUMERO_SERIE = O.NUMERO_SERIE

                WHERE S.ID_SAFRA = :id_safra
                AND A.DATA_HORA_INICIO >= S.DATA_HORA_PLANTIO
                AND A.DATA_HORA_FIM <= S.DATA_HORA_COLHEITA

                GROUP BY
                    A.ID_ATIVIDADE,
                    A.TIPO_ATIVIDADE,
                    A.DATA_HORA_INICIO,
                    A.DATA_HORA_FIM,
                    A.DURACAO,
                    A.AREA_TRABALHADA,
                    A.TEMPO_USO_MAQUINAS,
                    A.EMISSAO_CO2,
                    I.COD_BARRAS,
                    I.NOME,
                    I.TIPO

                ORDER BY A.DATA_HORA_INICIO
                """,
                {"id_safra": safra_id}
        )

        atividades = cursor.fetchall()

        print(f"\n-> CADEIA PRODUTIVA DA SAFRA {safra_id}\n")
        print("Atividades realizadas na Safra:")
        for a in atividades:
            print(f"- Atividade de ID: {a[0]} -")
            print(f"Tipo: {a[1]}")
            print(f"Início: {a[2]}")
            print(f"Fim: {a[3]}")
            print(f"Duração: {a[4]}")
            print(f"Área: {a[5]}")
            print(f"Emissão de CO2: {a[7]}")
            print(f"Insumo utilizado: {a[9]} ({a[10]})")
            print(f"Funcionários que a realizaram: {a[11]}")
            print(f"Máquinas utilizadas: {a[12]}")
            print()

        # Armazena os códigos de barras e nome dos agrotóxicos das atividades que usaram esse tipo de insumo
        codigos_agrotoxicos = set()

        for a in atividades:
            if a[10] == "AGROTOXICO":
                codigos_agrotoxicos.add((a[8], a[9]))  # código + nome


        if codigos_agrotoxicos:
            for cod, nome in codigos_agrotoxicos:

                cursor.execute(
                    """
                    SELECT
                        PC.NOME,
                        PC.CIDADE,
                        PC.ESTADO,
                        CD.DATA_DESCARTE,
                        CD.TIPO_DESCARTE,
                        CD.QUANTIDADE_DESCARTADA
                    FROM LISTADO_EM L

                    JOIN COMPROVANTE_DESCARTE CD
                        ON CD.CNPJ_PONTO_COLETA = L.CNPJ_PONTO_COLETA
                        AND CD.DATA_DESCARTE = L.DATA_DESCARTE

                    JOIN PONTO_COLETA PC
                        ON PC.CNPJ_PONTO_COLETA = CD.CNPJ_PONTO_COLETA

                    WHERE L.COD_BARRAS_AGROTOXICO = :cod
                    """,
                    {"cod": cod}
                )

                descartes = cursor.fetchall()

                print(f"\n-> Informações de descarte do agrotóxico {nome} (código {cod}):")

                if descartes:
                    for d in descartes:
                        print(f"Local: {d[0]} - {d[1]}/{d[2]}")
                        print(f"Data: {d[3]}")
                        print(f"Tipo: {d[4]}")
                        print(f"Quantidade: {d[5]}")
                else:
                    print("Nenhum descarte encontrado.")

        # Registro da consulta realizada
        cursor.execute(
            """
            INSERT INTO CONSULTA (ID_SAFRA, CPF_CNPJ_CLIENTE, DATA_HORA_CONSULTA)
            VALUES (:id_safra, :cpf, SYSDATE)
            """,
            {
                "id_safra": safra_id,
                "cpf": cpf_cliente
            }
        )

        conn.commit() # Encerra a transação
    
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")

def exibir_safras_futuras(conn):
    cursor = conn.cursor()

    print("\n-> O QUE VEM POR AÍ")

    try:
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(
            """
            SELECT 
                S.ID_SAFRA,
                S.NUM_LOTE,
                S.DATA_HORA_PLANTIO,
                S.DATA_HORA_COLHEITA,
                S.QUANTIDADE,
                L.CULTURA
            FROM SAFRA S
            JOIN LOTE_PLANTIO L
                ON L.COD_IMOVEL_RURAL = S.COD_IMOVEL_RURAL
                AND L.NUMERO = S.NUM_LOTE
            WHERE S.DATA_HORA_COLHEITA IS NULL
            """
        )

        safras = cursor.fetchall()

        if not safras:
            print("Nenhuma safra futura cadastrada.")
            return

        for safra in safras:
            print(f"\n- Safra de ID: {safra[0]} -")
            print(f"Lote: {safra[1]}")
            print(f"Cultura: {safra[5]}")
            print(f"Plantio: {safra[2]}")
            print(f"Quantidade prevista: {safra[4]}")
            print()

        conn.commit() # Encerra a transação

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")

def menu(conn, cpf_cliente):
    while(True):
        print("\n--- Menu do Cliente ---")
        print("1 - Consultar as informações desta Propriedade Rural")
        print("2 - Consultar processo produtivo acerca de uma Safra")
        print("3 - Consultar Safras futuras")
        print("0 - Voltar")

        opcao = int(input("\nEscolha uma opção para acessar: "))

        match opcao:
            case 1:
                consultar_propriedade(conn)
            case 2:
                exibir_safras_disponiveis(conn, cpf_cliente)
            case 3: 
                exibir_safras_futuras(conn)
            case 0: 
                print("Redirecionando...")
                return
            case _: 
                print("Opção desconhecida.")