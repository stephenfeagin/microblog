"""add_followers_table

Revision ID: 354591dfeea6
Revises: 86c46d9e1835
Create Date: 2019-11-09 19:04:24.938707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '354591dfeea6'
down_revision = '86c46d9e1835'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
