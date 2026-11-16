"""adiciona historico de renovacoes e controle de multas

Revision ID: c302dc9932c6
Revises:
Create Date: 2026-11-15 19:37:30.669289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c302dc9932c6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        'renovacoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emprestimo_id', sa.Integer(), nullable=False),
        sa.Column('numero_renovacao', sa.Integer(), nullable=False),
        sa.Column(
            'data_renovacao',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column('data_devolucao_anterior', sa.Date(), nullable=False),
        sa.Column('data_devolucao_nova', sa.Date(), nullable=False),
        sa.CheckConstraint(
            'numero_renovacao >= 1 AND numero_renovacao <= 5',
            name='ck_renovacao_numero'
        ),
        sa.ForeignKeyConstraint(
            ['emprestimo_id'],
            ['emprestimos.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_renovacoes_id'),
        'renovacoes',
        ['id'],
        unique=False
    )

    op.add_column(
        'emprestimos',
        sa.Column(
            'status_multa',
            sa.String(length=20),
            server_default='nao_aplicavel',
            nullable=False
        )
    )

    op.add_column(
        'emprestimos',
        sa.Column(
            'data_pagamento_multa',
            sa.Date(),
            nullable=True
        )
    )

    op.create_check_constraint(
        'ck_emprestimo_status_multa',
        'emprestimos',
        "status_multa IN ('nao_aplicavel', 'pendente', 'paga')"
    )



def downgrade() -> None:
    op.drop_constraint(
        'ck_emprestimo_status_multa',
        'emprestimos',
        type_='check'
    )
    op.drop_column('emprestimos', 'data_pagamento_multa')
    op.drop_column('emprestimos', 'status_multa')
    op.drop_index(op.f('ix_renovacoes_id'), table_name='renovacoes')
    op.drop_table('renovacoes')
