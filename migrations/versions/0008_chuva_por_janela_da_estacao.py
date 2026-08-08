"""Uma leitura por janela de CADA estação, não por relógio.

A 0007 consertou a inflação de 3× escolhendo "a leitura na marca" — minuto
múltiplo de 15. Isso vale para a coleta ao vivo, que consulta a origem nas
marcas, e **não vale para o histórico**: lá cada estação publica na fase dela.
Uma manda :01/:16/:31/:46, outra :02/:17/:32/:47, e o filtro por relógio jogou
fora quem não estava alinhada ao :00.

Medido na série completa, estações com dado contra estações que sobrevivem ao
filtro da 0007:

    1997-1999    26  ->   3
    2000-2002    28  ->   4
    2026 (vivo)  33  ->  33

Não é perda de precisão, é troca de população: a climatologia comparava a média
de 3 pluviômetros de 1997 com a rede inteira de hoje. O card existe justamente
para não fazer esse tipo de comparação.

O critério certo não é o relógio, é a janela: **uma leitura por bucket de 15 min
de cada estação**. `first(valor, ts)` cai na marca quando ela existe (era de 5
min, coleta ao vivo) e na fase própria da estação quando não existe (histórico),
sem precisar saber qual é a fase — a marca, quando existe, é a primeira do
bucket. E cobre o bucket em que a marca faltou, que a 0007 contava como zero.

Medido, com o agregado de 15 min no meio:

    ago/1997   3 est · 41,7 mm  ->  26 est · 51,6 mm
    fev/2020  33 est · 315,0 mm ->  33 est · 315,0 mm   (intocado: cadência de 15 min alinhada)
    fev/2024  33 est · 107,3 mm ->  33 est · 127,9 mm

fev/2020 não se mexe — é o controle que mostra que o método novo não move dado
que já estava certo. Os 20 mm de fev/2024 são quase todos de UMA estação com
leitura impossível (588 mm em 15 min, estação 8 em 17/02); isso é sujeira da
origem, tratada à parte, não efeito deste critério.

A hierarquia (agregado diário sobre o de 15 min) existe porque escolher uma
leitura por janela é uma agregação, e o diário precisa somar o resultado dela.
Não dá para fazer os dois numa consulta só de agregado contínuo.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-08
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

JANELA = """
    CREATE MATERIALIZED VIEW chuva_15min_estacao
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('15 minutes', ts) AS janela,
           local_id,
           first(valor, ts) AS mm
    FROM medicao
    WHERE metrica = 'chuva_15min'
    GROUP BY janela, local_id
    WITH NO DATA
"""

DIA_NOVO = """
    CREATE MATERIALIZED VIEW chuva_dia_estacao
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 day', janela, 'America/Sao_Paulo') AS dia,
           local_id,
           sum(mm) AS mm,
           count(*) AS leituras
    FROM chuva_15min_estacao
    GROUP BY dia, local_id
    WITH NO DATA
"""

DIA_0007 = """
    CREATE MATERIALIZED VIEW chuva_dia_estacao
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 day', ts, 'America/Sao_Paulo') AS dia,
           local_id,
           sum(valor) AS mm,
           count(*) AS leituras
    FROM medicao
    WHERE metrica = 'chuva_15min'
      AND EXTRACT(MINUTE FROM ts)::int % 15 = 0
    GROUP BY dia, local_id
    WITH NO DATA
"""

# O filho fecha 15 min antes do agora e roda a cada 15 min; o pai fecha 1 h
# depois e roda de hora em hora. Pai que enxergue além do filho materializa
# buraco: o dia corrente sairia menor do que é e voltaria ao normal sozinho na
# hora seguinte, que é pior que ficar um pouco atrasado.
POLITICA_JANELA = (
    "SELECT add_continuous_aggregate_policy('chuva_15min_estacao', "
    "start_offset => INTERVAL '7 days', "
    "end_offset => INTERVAL '15 minutes', "
    "schedule_interval => INTERVAL '15 minutes')"
)

POLITICA_DIA = (
    "SELECT add_continuous_aggregate_policy('chuva_dia_estacao', "
    "start_offset => INTERVAL '7 days', "
    "end_offset => INTERVAL '1 hour', "
    "schedule_interval => INTERVAL '1 hour')"
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        # O diário sai primeiro: com a hierarquia, ele passa a depender do de
        # 15 min, e o Postgres não deixa dropar o de baixo com o de cima em pé.
        op.execute("DROP MATERIALIZED VIEW IF EXISTS chuva_dia_estacao")
        op.execute(JANELA)
        op.execute(POLITICA_JANELA)
        op.execute(DIA_NOVO)
        op.execute(POLITICA_DIA)
        # Recriar zera a materialização, e a política só olha os últimos 7 dias:
        # sem isto o agregado nasce vazio e a climatologia responde "sem
        # histórico" com o banco cheio. Ordem importa — o pai lê o filho.
        op.execute("CALL refresh_continuous_aggregate('chuva_15min_estacao', NULL, NULL)")
        op.execute("CALL refresh_continuous_aggregate('chuva_dia_estacao', NULL, NULL)")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP MATERIALIZED VIEW IF EXISTS chuva_dia_estacao")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS chuva_15min_estacao")
        op.execute(DIA_0007)
        op.execute(POLITICA_DIA)
        op.execute("CALL refresh_continuous_aggregate('chuva_dia_estacao', NULL, NULL)")
