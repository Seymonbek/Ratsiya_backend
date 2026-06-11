from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Parol hash'lash testlari."""

    def test_hash_is_different_from_plain(self):
        """Hash ochiq paroldan farq qilishi kerak."""
        password = "mening_parolim123"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt formati

    def test_verify_correct_password(self):
        """To'g'ri parol tekshiruvdan o'tishi kerak."""
        password = "to'g'ri_parol"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Noto'g'ri parol rad etilishi kerak."""
        hashed = hash_password("haqiqiy_parol")
        assert verify_password("boshqa_parol", hashed) is False

    def test_same_password_different_hashes(self):
        """Bir xil parol har safar boshqa hash bersin (salt)."""
        password = "parol"
        assert hash_password(password) != hash_password(password)

    def test_long_password_truncated(self):
        """72 baytdan uzun parol ham xato bermasligi kerak."""
        long_password = "a" * 100  # 100 belgi
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True


class TestJWTToken:
    """JWT token testlari."""

    def test_create_and_decode(self):
        """Token yaratish va o'qish."""
        token = create_access_token(user_id=5, role="operator")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "5"
        assert payload["role"] == "operator"

    def test_invalid_token(self):
        """Yaroqsiz token None qaytarsin."""
        assert decode_access_token("yaroqsiz.token.string") is None

    def test_tampered_token(self):
        """O'zgartirilgan token rad etilsin."""
        token = create_access_token(user_id=1, role="driver")
        tampered = token[:-5] + "XXXXX"  # oxirini buzish
        assert decode_access_token(tampered) is None
