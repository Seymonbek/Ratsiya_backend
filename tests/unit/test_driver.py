import pytest
from fastapi import HTTPException

from app.enums import DriverStatus, UserRole
from app.core.permissions import check_is_operator, check_is_driver


class _FakeUser:
    """Test uchun soxta user."""
    def __init__(self, role, is_active=True):
        self.role = role
        self.is_active = is_active


class TestDriverStatus:
    """Driver status enum testlari."""

    def test_status_values(self):
        """TZ'dagi 3 ta status mavjud bo'lishi kerak."""
        assert DriverStatus.ONLINE == "online"
        assert DriverStatus.OFFLINE == "offline"
        assert DriverStatus.ON_TRIP == "on_trip"

    def test_only_three_statuses(self):
        """Faqat 3 ta status bo'lishi kerak."""
        assert len(list(DriverStatus)) == 3


class TestPermissions:
    """Rol tekshiruvi testlari (TZ qoidalari)."""

    def test_operator_passes_operator_check(self):
        """Operator — operator tekshiruvidan o'tadi."""
        user = _FakeUser(UserRole.OPERATOR)
        check_is_operator(user)  # xato bermasligi kerak

    def test_driver_fails_operator_check(self):
        """Driver — operator tekshiruvidan o'tmaydi (403)."""
        user = _FakeUser(UserRole.DRIVER)
        with pytest.raises(HTTPException) as exc:
            check_is_operator(user)
        assert exc.value.status_code == 403

    def test_driver_passes_driver_check(self):
        """Driver — driver tekshiruvidan o'tadi."""
        user = _FakeUser(UserRole.DRIVER)
        check_is_driver(user)

    def test_operator_fails_driver_check(self):
        """Operator — driver tekshiruvidan o'tmaydi (403)."""
        user = _FakeUser(UserRole.OPERATOR)
        with pytest.raises(HTTPException) as exc:
            check_is_driver(user)
        assert exc.value.status_code == 403
