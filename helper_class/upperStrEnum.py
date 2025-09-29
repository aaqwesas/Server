from enum import StrEnum
from abc import ABCMeta
from typing import Any


class UpperStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, *args):
        return name.upper()
