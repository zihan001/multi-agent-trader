"""update_agent_logs_table_for_llm_tracking

Revision ID: 0e6ebfdb000c
Revises: 85dbcbd4be98
Create Date: 2025-11-18 02:57:50.938762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e6ebfdb000c'
down_revision = '85dbcbd4be98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old columns
    op.drop_column('agent_logs', 'decision_id')
    op.drop_column('agent_logs', 'input_summary')
    op.drop_column('agent_logs', 'output_summary')
    
    # Rename/modify existing columns
    op.alter_column('agent_logs', 'model_name', new_column_name='model', existing_type=sa.String(50))
    op.alter_column('agent_logs', 'model', type_=sa.String(100), existing_type=sa.String(50))
    op.alter_column('agent_logs', 'tokens_input', new_column_name='input_tokens')
    op.alter_column('agent_logs', 'tokens_output', new_column_name='output_tokens')
    op.alter_column('agent_logs', 'cost_estimate', new_column_name='cost')
    
    # Add new columns
    op.add_column('agent_logs', sa.Column('input_data', sa.Text(), nullable=True))
    op.add_column('agent_logs', sa.Column('output_data', sa.Text(), nullable=True))
    op.add_column('agent_logs', sa.Column('tokens_used', sa.Integer(), default=0))
    op.add_column('agent_logs', sa.Column('latency_seconds', sa.Float(), nullable=True))
    
    # Make run_id nullable
    op.alter_column('agent_logs', 'run_id', nullable=True, existing_type=sa.String(50))
    
    # Add index on symbol if not exists
    op.create_index(op.f('ix_agent_logs_symbol'), 'agent_logs', ['symbol'], unique=False)


def downgrade() -> None:
    # Remove new columns
    op.drop_column('agent_logs', 'latency_seconds')
    op.drop_column('agent_logs', 'tokens_used')
    op.drop_column('agent_logs', 'output_data')
    op.drop_column('agent_logs', 'input_data')
    
    # Revert column renames
    op.alter_column('agent_logs', 'cost', new_column_name='cost_estimate')
    op.alter_column('agent_logs', 'output_tokens', new_column_name='tokens_output')
    op.alter_column('agent_logs', 'input_tokens', new_column_name='tokens_input')
    op.alter_column('agent_logs', 'model', type_=sa.String(50), existing_type=sa.String(100))
    op.alter_column('agent_logs', 'model', new_column_name='model_name', existing_type=sa.String(50))
    
    # Make run_id non-nullable again
    op.alter_column('agent_logs', 'run_id', nullable=False, existing_type=sa.String(50))
    
    # Drop symbol index
    op.drop_index(op.f('ix_agent_logs_symbol'), table_name='agent_logs')
    
    # Add back old columns
    op.add_column('agent_logs', sa.Column('decision_id', sa.String(50), nullable=True))
    op.add_column('agent_logs', sa.Column('input_summary', sa.JSON(), nullable=True))
    op.add_column('agent_logs', sa.Column('output_summary', sa.JSON(), nullable=True))
    
    # Recreate decision_id index
    op.create_index('ix_agent_logs_decision_id', 'agent_logs', ['decision_id'], unique=False)