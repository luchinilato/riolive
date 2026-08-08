"""Zona popular por Região Administrativa.

O painel promete recorte territorial e a cidade não tem essa divisão em lugar
nenhum do banco: existem 33 RAs e 166 bairros, e nenhuma coluna que responda
"isto é Zona Norte".

**Zona popular não é divisão oficial.** A Prefeitura organiza por Áreas de
Planejamento (AP 1 a 5); "Zona Sul" é como o carioca fala, não como o município
administra. Escolhemos a fala — o painel é para quem vive aqui — e por isso o
mapeamento é NOSSO e fica declarado aqui, não escondido numa consulta.

Os três pontos em que gente razoável discorda, e o que decidimos:

- **Barra da Tijuca e Jacarepaguá → Zona Oeste.** É a leitura mais comum, ainda
  que muito morador da Barra diga só "Barra".
- **Paquetá → Centro.** A ilha pertence à AP1 com o Centro; classificá-la como
  Zona Norte por proximidade da Ilha do Governador seria invenção nossa.
- **Rocinha → Zona Sul.** Fica entre São Conrado e a Gávea, e é RA própria
  desde 1993.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

# Nomes exatos como estão em `ra.nome` (sem acento onde a carga não tem).
ZONAS: dict[str, tuple[str, ...]] = {
    "centro": ("PORTUARIA", "CENTRO", "RIO COMPRIDO", "SAO CRISTOVAO", "SANTA TEREZA", "PAQUETA"),
    "sul": ("BOTAFOGO", "COPACABANA", "LAGOA", "ROCINHA"),
    "norte": (
        "TIJUCA",
        "VILA ISABEL",
        "RAMOS",
        "PENHA",
        "INHAUMA",
        "MEIER",
        "IRAJA",
        "MADUREIRA",
        "ILHA DO GOVERNADOR",
        "ANCHIETA",
        "PAVUNA",
        "JACAREZINHO",
        "COMPLEXO DO ALEMÃO",
        "COMPLEXO DA MARE",
        "VIGARIO GERAL",
    ),
    "oeste": (
        "JACAREPAGUA",
        "BANGU",
        "CAMPO GRANDE",
        "SANTA CRUZ",
        "BARRA DA TIJUCA",
        "GUARATIBA",
        "REALENGO",
        "CIDADE DE DEUS",
    ),
}


def upgrade() -> None:
    op.add_column("ra", sa.Column("zona", sa.String(16), nullable=True))
    for zona, ras in ZONAS.items():
        op.execute(
            sa.text("UPDATE ra SET zona = :z WHERE nome = ANY(:nomes)").bindparams(
                sa.bindparam("z", value=zona), sa.bindparam("nomes", value=list(ras))
            )
        )
    op.create_index("idx_ra_zona", "ra", ["zona"])

    # RA sem zona não dá erro em lugar nenhum: ela apenas some de todo filtro
    # territorial, para sempre e em silêncio. Um "SANTA TERESA" no lugar de
    # "SANTA TEREZA" já foi suficiente para deixar uma de fora — por isso a
    # migration falha aqui em vez de deixar o buraco passar.
    orfas = (
        op.get_bind()
        .execute(sa.text("SELECT string_agg(nome, ', ') FROM ra WHERE zona IS NULL"))
        .scalar()
    )
    if orfas:
        raise RuntimeError(f"RA sem zona (nome divergente do mapeamento?): {orfas}")


def downgrade() -> None:
    op.drop_index("idx_ra_zona", table_name="ra")
    op.drop_column("ra", "zona")
