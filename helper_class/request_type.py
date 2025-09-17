from enum import auto

from helper_class.upperStrEnum import UpperStrEnum



class Request_Type(UpperStrEnum):
    POST = auto()
    GET = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()
    
