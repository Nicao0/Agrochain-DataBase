--- Consulta 1 ---

-- Recupera o histórico completo de atividades agrícolas associadas a uma safra específica, 
-- retornando os dados operacionais, os funcionários responsáveis, as máquinas utilizadas 
-- (com seus respectivos combustíveis) e os insumos empregados.
-- Nota: Esta consulta atua em conjunto com a rotina de rastreabilidade de descarte 
-- de agrotóxicos e registra automaticamente a auditoria de acesso na entidade CONSULTA.
-- Para fins de teste, foi parametrizada a Safra de ID 2.

SELECT
    A.ID_ATIVIDADE,
    A.TIPO_ATIVIDADE,
    A.DATA_HORA_INICIO,
    A.DATA_HORA_FIM,
    A.DURACAO AS DURACAO_EM_HORAS,
    A.AREA_TRABALHADA,
    A.TEMPO_USO_MAQUINAS AS TEMPO_USO_MAQUINAS_EM_HORAS,
    A.EMISSAO_CO2,

    I.COD_BARRAS,
    I.NOME AS NOME_INSUMO,
    I.TIPO AS TIPO_INSUMO,

    -- Agrega os nomes dos funcionários em uma única string, 
    -- evitando a duplicação de tuplas para a mesma atividade
    LISTAGG(
        DISTINCT P.NOME,
        ', '
    ) WITHIN GROUP (ORDER BY P.NOME)
        AS FUNCIONARIOS,

    -- Agrega as máquinas utilizadas e o combustível em uso no momento da atividade
    LISTAGG(
        DISTINCT
        M.NUMERO_SERIE ||
        ' - ' ||
        M.MODELO ||
        ' (' ||
        M.COMBUSTIVEL_EM_USO ||
        ')',
        ' | '
    ) WITHIN GROUP (ORDER BY M.NUMERO_SERIE)
        AS MAQUINAS

FROM SAFRA S

-- Estabelece a junção com o lote correspondente ao ciclo da safra
JOIN ATIVIDADE_AGRICOLA A
ON A.COD_IMOVEL_RURAL = S.COD_IMOVEL_RURAL
AND A.NUM_LOTE = S.NUM_LOTE

-- Preserva as atividades agrícolas que não empregaram nenhum tipo de insumo
LEFT JOIN INSUMO I
ON I.COD_BARRAS = A.COD_BARRAS_INSUMO

-- Utiliza INNER JOIN pois toda atividade possui obrigatoriamente ao menos um funcionário
JOIN REALIZADA_POR R
ON R.ID_ATIVIDADE = A.ID_ATIVIDADE

JOIN FUNCIONARIO F
ON F.CPF_CNPJ = R.CPF_CNPJ_FUNC

JOIN PESSOA P
ON P.CPF_CNPJ = F.CPF_CNPJ

-- Preserva as atividades de execução puramente manual (sem maquinário associado)
LEFT JOIN OPERA O
ON O.ID_ATIVIDADE = A.ID_ATIVIDADE

LEFT JOIN MAQUINA M
ON M.NUMERO_SERIE = O.NUMERO_SERIE

-- Restringe a busca à safra parametrizada e ao intervalo temporal em que esteve plantada
WHERE S.ID_SAFRA = 2
AND A.DATA_HORA_INICIO >= S.DATA_HORA_PLANTIO
AND A.DATA_HORA_FIM <= S.DATA_HORA_COLHEITA

GROUP BY
    S.ID_SAFRA,

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

-- Organiza o histórico operacional de forma cronológica ascendente
ORDER BY A.DATA_HORA_INICIO;

-- Rastreabilidade Complementar de Descarte de Agrotóxicos (Aplicação)
-- Recupera formalmente as informações de descarte e os pontos de coleta 
-- associados aos agrotóxicos aplicados nas atividades da safra consultada.
-- Para fins de teste, utilizou-se o código de barras do agrotóxico 7890000000002.

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

WHERE L.COD_BARRAS_AGROTOXICO = 7890000000002;

-- Auditoria de Acesso à Safra
-- Registra de forma automatizada toda consulta realizada por um cliente ao 
-- histórico de rastreabilidade de uma safra.
-- Para fins de teste, simulou-se a consulta pelo cliente de CPF 77777777777 à Safra 2.

INSERT INTO CONSULTA(ID_SAFRA, CPF_CNPJ_CLIENTE, DATA_HORA_CONSULTA)
VALUES(2, 77777777777, SYSDATE);

--- Consulta 2 ---

-- Gera um ranking de sustentabilidade das safras cadastradas, classificando-as 
-- prioritariamente pela ausência de agrotóxicos, seguidas pela menor toxicidade 
-- (Classes I a III) e, como critério de desempate, pela menor emissão total de CO2.

SELECT 
    S.ID_SAFRA,
    LP.CULTURA,
    MAX(
        CASE 
            WHEN AG.CLASSE_TOXICOLOGICA IS NULL THEN 'SEM AGROTOXICO'
            ELSE AG.CLASSE_TOXICOLOGICA 
        END
    ) AS STATUS_AGROTOXICO,
    SUM(AA.EMISSAO_CO2) AS TOTAL_EMISSAO_CO2
    
FROM SAFRA S

INNER JOIN LOTE_PLANTIO LP 
    ON S.COD_IMOVEL_RURAL = LP.COD_IMOVEL_RURAL 
    AND S.NUM_LOTE = LP.NUMERO
    
-- Preserva as safras que ainda não possuem atividades agrícolas registradas no período
LEFT JOIN ATIVIDADE_AGRICOLA AA 
    ON S.COD_IMOVEL_RURAL = AA.COD_IMOVEL_RURAL 
    AND S.NUM_LOTE = AA.NUM_LOTE
    AND AA.DATA_HORA_INICIO >= S.DATA_HORA_PLANTIO 
    AND (
        AA.DATA_HORA_INICIO <= S.DATA_HORA_COLHEITA 
        OR S.DATA_HORA_COLHEITA IS NULL
    )

-- Preserva as atividades agrícolas que não empregaram insumos do tipo agrotóxico
LEFT JOIN AGROTOXICO AG 
    ON AA.COD_BARRAS_INSUMO = AG.COD_BARRAS

-- Agrupa pela safra e cultura para viabilizar a agregação do status toxicológico e a soma de CO2
GROUP BY 
    S.ID_SAFRA, 
    LP.CULTURA

-- Converte as classes textuais em pesos numéricos para garantir a ordenação correta da toxicidade, 
-- aplicando a soma de emissão de CO2 como critério secundário (desempate)
ORDER BY 
    MAX(
        CASE 
            WHEN AG.CLASSE_TOXICOLOGICA IS NULL THEN 0
            WHEN AG.CLASSE_TOXICOLOGICA = 'CLASSE I' THEN 1
            WHEN AG.CLASSE_TOXICOLOGICA = 'CLASSE II' THEN 2
            WHEN AG.CLASSE_TOXICOLOGICA = 'CLASSE III' THEN 3
        END
    ) ASC,
    SUM(AA.EMISSAO_CO2) ASC;
    
--- Consulta 3 ---

-- Recupera o histórico operacional completo de um lote de plantio específico, 
-- exibindo: dados do lote, a atividade executada, a duração, a área trabalhada, 
-- os funcionários envolvidos, as máquinas utilizadas (com tempo de uso) 
-- e a emissão de CO2 associada.
-- Para fins de teste, foi escolhido o lote 1 da propriedade rural 123456.

SELECT 
    L.NUMERO AS LOTE,
    L.CULTURA,
    
    A.TIPO_ATIVIDADE,
    A.DATA_HORA_INICIO,
    A.DURACAO AS DURACAO_HORAS,
    A.AREA_TRABALHADA,
    A.EMISSAO_CO2,
    
    -- Agrega os nomes dos funcionários em uma única string, 
    -- evitando a duplicação de linhas para a mesma atividade
    LISTAGG(DISTINCT P.NOME, ', ') 
        WITHIN GROUP (ORDER BY P.NOME) 
        AS FUNCIONARIOS,

    -- Agrega as máquinas utilizadas e o tempo de operação de cada uma
    LISTAGG(DISTINCT 
        M.TIPO || ' - ' || M.MODELO || ' (' || O.TEMPO_USO || 'h)',
        ' | '
    ) WITHIN GROUP (ORDER BY M.NUMERO_SERIE)
        AS MAQUINAS
        
FROM LOTE_PLANTIO L

-- Preserva os lotes que ainda não tiveram atividades agrícolas associadas
LEFT JOIN ATIVIDADE_AGRICOLA A 
    ON L.COD_IMOVEL_RURAL = A.COD_IMOVEL_RURAL 
   AND L.NUMERO = A.NUM_LOTE
   
-- Utiliza INNER JOIN pois toda atividade realizada possui ao menos um funcionário
JOIN REALIZADA_POR R 
    ON A.ID_ATIVIDADE = R.ID_ATIVIDADE
    
JOIN PESSOA P 
    ON R.CPF_CNPJ_FUNC = P.CPF_CNPJ

-- Preserva atividades em que nenhuma máquina foi utilizada (trabalho manual)
LEFT JOIN OPERA O 
    ON A.ID_ATIVIDADE = O.ID_ATIVIDADE
    
LEFT JOIN MAQUINA M 
    ON O.NUMERO_SERIE = M.NUMERO_SERIE
    
-- Filtra especificamente o lote de teste
WHERE L.COD_IMOVEL_RURAL = 123456 
  AND L.NUMERO = 1
  
GROUP BY 
    L.NUMERO,
    L.CULTURA,
    A.TIPO_ATIVIDADE,
    A.DATA_HORA_INICIO,
    A.DURACAO,
    A.AREA_TRABALHADA,
    A.EMISSAO_CO2

-- Organiza o histórico de forma cronológica
ORDER BY A.DATA_HORA_INICIO ASC;

--- Consulta 4 ---

-- Esta consulta gera um relatório geral da propriedade rural, 
-- agrupando os lotes por status: LIVRE, OCUPADO e EM PREPARO. 
-- A ideia é mostrar, para cada status: 
-- quantidade de lotes, 
-- área total, 
-- percentual da área total da propriedade, 
-- quantidade de atividades, 
-- quantidade de funcionários envolvidos, 
-- quantidade de máquinas utilizadas 
-- e emissão total de CO2.

WITH STATUS_LOTE AS (
    -- Criamos manualmente a lista de status possíveis dos lotes. 
    -- Isso garante que os três status apareçam no resultado final, 
    -- mesmo que algum deles não tenha nenhum lote cadastrado.
    -- Usamos UNION ALL porque não precisamos remover duplicatas.
    -- Como os valores 'LIVRE', 'OCUPADO' e 'EM PREPARO' já são diferentes, 
    -- UNION ALL é mais adequado e mais eficiente do que UNION.
    SELECT 'LIVRE' AS STATUS FROM DUAL
    UNION ALL 
    SELECT 'OCUPADO' FROM DUAL
    UNION ALL
    SELECT 'EM PREPARO' FROM DUAL
),

RESUMO_LOTES AS (
    -- Agrupa os lotes por status.
    -- Para cada status, calcula: 
    -- 1. quantidade de lotes; 
    -- 2. soma da área total dos lotes daquele status.
    SELECT
        STATUS,
        COUNT(*) AS QTD_LOTES,
        SUM(AREA_TOTAL) AS AREA_TOTAL_STATUS
    FROM LOTE_PLANTIO
    GROUP BY STATUS
),

AREA_GERAL AS (
    -- Calcula a área total da propriedade considerando todos os lotes. 
    -- Esse valor será usado depois para calcular o percentual de área 
    -- correspondente a cada status.
    SELECT
        SUM(AREA_TOTAL) AS AREA_TOTAL_PROPRIEDADE
    FROM LOTE_PLANTIO
),

RESUMO_ATIVIDADES AS (
    -- Calcula, para cada status de lote: 
    -- 1. a quantidade de atividades agrícolas distintas; 
    -- 2. a emissão total de CO2 dessas atividades. 
    -- O LEFT JOIN é usado para manter os lotes no resultado 
    -- mesmo quando eles não possuem atividades associadas.
    SELECT
        L.STATUS,
        COUNT(DISTINCT A.ID_ATIVIDADE) AS QTD_ATIVIDADES,
        SUM(A.EMISSAO_CO2) AS EMISSAO_TOTAL_CO2
    FROM LOTE_PLANTIO L
    LEFT JOIN ATIVIDADE_AGRICOLA A
        ON A.COD_IMOVEL_RURAL = L.COD_IMOVEL_RURAL
       AND A.NUM_LOTE = L.NUMERO
    GROUP BY L.STATUS
),

RESUMO_FUNCIONARIOS AS (
    -- Calcula a quantidade de funcionários distintos envolvidos 
    -- nas atividades agrícolas de lotes agrupados por status. 
    -- Primeiro ligamos o lote à atividade. 
    -- Depois ligamos a atividade à tabela REALIZADA_POR, 
    -- que indica quais funcionários participaram de cada atividade.
    SELECT
        L.STATUS,
        COUNT(DISTINCT RP.CPF_CNPJ_FUNC) AS QTD_FUNCIONARIOS
    FROM LOTE_PLANTIO L
    LEFT JOIN ATIVIDADE_AGRICOLA A
        ON A.COD_IMOVEL_RURAL = L.COD_IMOVEL_RURAL
       AND A.NUM_LOTE = L.NUMERO
    LEFT JOIN REALIZADA_POR RP
        ON RP.ID_ATIVIDADE = A.ID_ATIVIDADE
    GROUP BY L.STATUS
),

RESUMO_MAQUINAS AS (
    -- Calcula a quantidade de máquinas distintas utilizadas 
    -- nas atividades agrícolas de lotes agrupados por status. 
    -- A tabela OPERA representa a relação entre máquinas e atividades.
    SELECT
        L.STATUS,
        COUNT(DISTINCT O.NUMERO_SERIE) AS QTD_MAQUINAS
    FROM LOTE_PLANTIO L
    LEFT JOIN ATIVIDADE_AGRICOLA A
        ON A.COD_IMOVEL_RURAL = L.COD_IMOVEL_RURAL
       AND A.NUM_LOTE = L.NUMERO
    LEFT JOIN OPERA O
        ON O.ID_ATIVIDADE = A.ID_ATIVIDADE
    GROUP BY L.STATUS
)

SELECT
    -- Status do lote: LIVRE, OCUPADO ou EM PREPARO.
    S.STATUS,
    -- Quantidade de lotes existentes naquele status.
    RL.QTD_LOTES,
    -- Área total ocupada pelos lotes daquele status.
    RL.AREA_TOTAL_STATUS AS AREA_TOTAL,
    -- Calcula o percentual da área daquele status em relação à área total. 
    -- NULLIF evita divisão por zero caso a área total da propriedade seja 0. 
    -- ROUND arredonda o resultado para 2 casas decimais.
    ROUND(
        RL.AREA_TOTAL_STATUS / NULLIF(AG.AREA_TOTAL_PROPRIEDADE, 0) * 100,
        2
    ) AS PERCENTUAL_AREA,
    -- Quantidade de atividades agrícolas relacionadas aos lotes desse status.
    RA.QTD_ATIVIDADES,
    -- Quantidade de funcionários distintos envolvidos nessas atividades.
    RF.QTD_FUNCIONARIOS,
    -- Quantidade de máquinas distintas utilizadas nessas atividades.
    RM.QTD_MAQUINAS,
    -- Emissão total de CO2 das atividades ligadas aos lotes desse status.
    RA.EMISSAO_TOTAL_CO2
    
FROM STATUS_LOTE S

CROSS JOIN AREA_GERAL AG 
-- Usamos CROSS JOIN porque AREA_GERAL retorna apenas uma linha, 
-- contendo a área total da propriedade. 
-- Assim, esse valor único é associado a cada status da lista STATUS_LOTE, 
-- permitindo calcular o percentual de área para LIVRE, OCUPADO e EM PREPARO.

LEFT JOIN RESUMO_LOTES RL
    ON RL.STATUS = S.STATUS
-- Junta o resumo dos lotes com a lista fixa de status. 
-- O LEFT JOIN garante que o status continue aparecendo 
-- mesmo se não houver lote com aquele status.    
LEFT JOIN RESUMO_ATIVIDADES RA
    ON RA.STATUS = S.STATUS
-- Junta as informações de atividades e emissão de CO2.    
LEFT JOIN RESUMO_FUNCIONARIOS RF
    ON RF.STATUS = S.STATUS
-- Junta a quantidade de funcionários envolvidos nas atividades.    
LEFT JOIN RESUMO_MAQUINAS RM
    ON RM.STATUS = S.STATUS
-- Junta a quantidade de máquinas utilizadas nas atividades.   
ORDER BY
    -- Define uma ordem personalizada para os status, 
    -- em vez de ordenar alfabeticamente.
    CASE S.STATUS
        WHEN 'LIVRE' THEN 1
        WHEN 'OCUPADO' THEN 2
        WHEN 'EM PREPARO' THEN 3
    END;
    
--- Consulta 5 ---

-- Essa consulta utiliza divisão relacional, visando responder a seguinte questão:
-- Qual(is) funcionário(os) participaram de todas as atividades agrícolas realizadas no 
-- lote 1 da propriedade
-- Em outras palavras: 
-- queremos encontrar funcionários para os quais NÃO exista nenhuma atividade 
-- do lote 1 da propriedade 123456 em que eles NÃO tenham participado. 
-- -- A lógica da divisão relacional aqui é: 
-- selecionar o funcionário F tal que, para toda atividade A do lote escolhido, 
-- exista um registro em REALIZADA_POR ligando F a A.

SELECT 
    -- CPF/CNPJ e o nome associado ao funcionário
    F.CPF_CNPJ,
    P.NOME
    
FROM FUNCIONARIO F

JOIN PESSOA P
    -- Junta FUNCIONARIO com PESSOA para obter o nome do funcionário. 
    -- A tabela FUNCIONARIO guarda os dados específicos do funcionário, 
    -- enquanto PESSOA guarda dados gerais, como o nome. 
    ON P.CPF_CNPJ = F.CPF_CNPJ
 
WHERE EXISTS (
    -- Este EXISTS verifica se realmente existe pelo menos uma atividade 
    -- no lote 1 da propriedade 123456. 
    -- Isso evita um problema da divisão relacional chamado "verdade vazia". 
    -- Sem esse EXISTS, se não existisse nenhuma atividade no lote, 
    -- todos os funcionários poderiam aparecer no resultado, 
    -- porque não haveria nenhuma atividade faltando para eles.
    SELECT 1
    
    FROM ATIVIDADE_AGRICOLA A
    
    WHERE A.COD_IMOVEL_RURAL = 123456
      AND A.NUM_LOTE = 1
)

AND NOT EXISTS (
    -- Aqui começa a parte principal da divisão relacional. 
    -- Procuramos uma atividade do lote 1 da propriedade 123456 
    -- para a qual o funcionário F NÃO tenha participado. 
    -- Se essa atividade existir, o funcionário não serve. 
    -- Se essa atividade NÃO existir, significa que o funcionário participou 
    -- de todas as atividades daquele lote.
    SELECT 1
    
    FROM ATIVIDADE_AGRICOLA A
    
    WHERE A.COD_IMOVEL_RURAL = 123456
      AND A.NUM_LOTE = 1
      
      AND NOT EXISTS (
        -- Este NOT EXISTS interno verifica se não existe uma relação 
        -- entre a atividade A e o funcionário F na tabela REALIZADA_POR. 
        -- REALIZADA_POR registra quais funcionários participaram 
        -- de quais atividades.
          SELECT 1
          FROM REALIZADA_POR RP
          WHERE RP.ID_ATIVIDADE = A.ID_ATIVIDADE
            AND RP.CPF_CNPJ_FUNC = F.CPF_CNPJ
      )
);