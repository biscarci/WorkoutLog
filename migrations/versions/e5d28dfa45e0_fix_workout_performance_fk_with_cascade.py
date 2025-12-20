from alembic import op
import sqlalchemy as sa

revision = 'e5d28dfa45e0'
down_revision = 'e875072df6b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        'workout_performance',
        recreate='always'
    ) as batch_op:
        batch_op.create_foreign_key(
            'fk_wp_workout',
            'workout',
            ['workout_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_wp_performance',
            'performance',
            ['performance_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    with op.batch_alter_table(
        'workout_performance',
        recreate='always'
    ) as batch_op:
        batch_op.create_foreign_key(
            'fk_wp_workout',
            'workout',
            ['workout_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_wp_performance',
            'performance',
            ['performance_id'],
            ['id']
        )
