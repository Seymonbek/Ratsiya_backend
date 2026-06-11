from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migratsiyani qo'llash yangi versiyaga o'tish."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Migratsiyani bekor qilish eski versiyaga qaytish."""
    ${downgrades if downgrades else "pass"}
