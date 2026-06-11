from enum import Enum


class DriverStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ON_TRIP = "on_trip"
