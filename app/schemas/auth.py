from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Login nomi (3-50 belgi)",
        examples=["ali_operator"],
    )
    password: str = Field(
        min_length=6,
        max_length=100,
        description="Parol (kamida 6 belgi)",
        examples=["xavfsiz_parol123"],
    )
    full_name: str = Field(
        min_length=2,
        max_length=100,
        description="To'liq ism",
        examples=["Ali Valiyev"],
    )


class DriverRegisterRequest(RegisterRequest):

    license_plate: str = Field(
        min_length=4,
        max_length=20,
        description="Mashina raqami",
        examples=["90A123PA"],
    )


class LoginRequest(BaseModel):

    username: str = Field(
        description="Login nomi",
        examples=["ali_operator"],
    )
    password: str = Field(
        description="Parol",
        examples=["xavfsiz_parol123"],
    )


class TokenResponse(BaseModel):

    access_token: str = Field(
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token turi (doim 'bearer')",
    )
