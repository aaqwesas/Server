from enum import auto

from helper_class.upperStrEnum import UpperStrEnum



class RequestType(UpperStrEnum):
    POST = auto()
    GET = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()
    
