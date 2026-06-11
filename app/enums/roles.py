from enum import Enum


class UserRole(str, Enum):
    OPERATOR = "operator"
    DRIVER = "driver"
