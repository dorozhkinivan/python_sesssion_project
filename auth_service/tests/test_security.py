from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_not_equal_to_plain(self):
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password

    def test_verify_correct_password(self):
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_access_token(sub="42", role="user")
        payload = decode_token(token)

        assert payload["sub"] == "42"
        assert payload["role"] == "user"
        assert "iat" in payload
        assert "exp" in payload

    def test_token_with_admin_role(self):
        token = create_access_token(sub="1", role="admin")
        payload = decode_token(token)

        assert payload["sub"] == "1"
        assert payload["role"] == "admin"

    def test_token_with_custom_expiry(self):
        token = create_access_token(
            sub="10",
            role="user",
            expires_delta=timedelta(minutes=5),
        )
        payload = decode_token(token)

        assert payload["sub"] == "10"
        assert payload["exp"] > payload["iat"]

    def test_expired_token_raises(self):
        from jose import ExpiredSignatureError

        token = create_access_token(
            sub="1",
            role="user",
            expires_delta=timedelta(seconds=-1),
        )
        try:
            decode_token(token)
            assert False, "Should have raised"
        except ExpiredSignatureError:
            pass

    def test_invalid_token_raises(self):
        from jose import JWTError

        try:
            decode_token("not.a.valid.token")
            assert False, "Should have raised"
        except JWTError:
            pass
