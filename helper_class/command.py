from enum import StrEnum, auto



class Command(StrEnum):
    START = auto()
    STOP = auto()
    LIST = auto()
    STATUS = auto()
    HEALTH = auto()


