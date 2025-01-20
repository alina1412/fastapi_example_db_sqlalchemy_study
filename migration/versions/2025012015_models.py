"""models

Revision ID: 671002e2e27d
Revises: 19ac466950ed
Create Date: 2025-01-20 15:53:59.853940

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from sqlalchemy.engine.reflection import Inspector


conn = op.get_bind()
inspector = Inspector.from_engine(conn)
tables = inspector.get_table_names()


# revision identifiers, used by Alembic.
revision: str = '671002e2e27d'
down_revision: Union[str, None] = '19ac466950ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('player',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('score', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_id')
    )
    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('active', sa.Integer(), nullable=False),
    sa.Column('updated_dt', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tg_update',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Integer(), server_default='1', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('answer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=255), nullable=True),
    sa.Column('correct', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('round',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('asked', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['player.tg_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('round')
    op.drop_table('answer')
    op.drop_table('user')
    op.drop_table('tg_update')
    op.drop_table('question')
    op.drop_table('player')
    # ### end Alembic commands ###
