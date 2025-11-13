"""Create initial schema with products, webhooks, and jobs tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-13 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(255), nullable=False),
        sa.Column('sku_norm', sa.String(255), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for products
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('ix_products_sku_norm', 'products', ['sku_norm'], unique=True)
    op.create_index('ix_products_name', 'products', ['name'], unique=False)
    op.create_index('ix_products_active', 'products', ['active'], unique=False)
    op.create_index('ix_products_sku_norm_active', 'products', ['sku_norm', 'active'], unique=False)
    
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('event_types', sa.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_response_status', sa.Integer(), nullable=True),
        sa.Column('last_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for webhooks
    op.create_index('ix_webhooks_id', 'webhooks', ['id'], unique=False)
    op.create_index('ix_webhooks_enabled', 'webhooks', ['enabled'], unique=False)
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('processed_rows', sa.Integer(), nullable=True),
        sa.Column('created_rows', sa.Integer(), nullable=True),
        sa.Column('updated_rows', sa.Integer(), nullable=True),
        sa.Column('failed_rows', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(100), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('celery_task_id', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for jobs
    op.create_index('ix_jobs_id', 'jobs', ['id'], unique=False)
    op.create_index('ix_jobs_job_id', 'jobs', ['job_id'], unique=True)
    op.create_index('ix_jobs_status', 'jobs', ['status'], unique=False)
    op.create_index('ix_jobs_celery_task_id', 'jobs', ['celery_task_id'], unique=False)


def downgrade() -> None:
    """Revert schema."""
    op.drop_table('jobs')
    op.drop_table('webhooks')
    op.drop_table('products')
