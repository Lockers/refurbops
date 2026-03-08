from enum import StrEnum


class DeviceStatus(StrEnum):
    EXPECTED = "expected"
    ARRIVED = "arrived"
    LABEL_PRINTED = "label_printed"
