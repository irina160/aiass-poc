from dataclasses import dataclass
from typing import Any, Dict, Union, get_args, get_origin
from customerrors import NotAValidInstance, NotAValidPostRequest
import numbers


@dataclass
class BaseSchema:
    """
    Every schema that inherits from this class needs to type its items as precise as possible.

    Allowed:
        item: str (or any other base type like number, float, etc.)
        item: List[CUSTOMTYPE]
        item: Dict[str, CUSTOMTYPE]

    Not Allowed:
        item: Dict[str, Any] (or any combinations of base types)
        item: List[Dict[str, Any]] (or any combination of base types)

    .. highlight:: python
    .. code-block:: python
    Example:
        @dataclass
        class MyDataclass(BaseSchema):
            id: str
            settings: Dict[str, Settings]

        @dataclass
        class Settings(BaseSchema):
            id: str
            name: str

    Example:
        @dataclass
        class UseCaseTypeSchema(BaseSchema):
            id: str
            name_de: str
            name_en: str
            features: Dict[str, Dict[str, Dict[str, str]]]
            indices: Optional[List[IndexSchema]] = field(default_factory=list)


        @dataclass
        class Features(BaseSchema):
            general: Dict[str, Settings]
            indices: Dict[str, Settings]
            categories: Dict[str, Settings]
            chat: Dict[str, Settings]
            overrides: Dict[str, Settings]


        @dataclass
        class Settings(baseSchema):
            ... #further items
    """

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._validate_attributes(kwargs)
        return self

    def _validate_attributes(self, kwargs):
        for attr, value in kwargs.items():
            if value is None:
                raise ValueError(f"Missing value for attribute '{attr}'")
            if attr not in list(self.__dataclass_fields__.keys()):
                raise ValueError(
                    f"Provided attribute {attr} does not exists on type {self.__class__}"
                )
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) or isinstance(item, numbers.Number):
                        # We assume something like List[str] is used, therefore no need to check further. No typechecking here! i.e. field: List[str] but List[int] is provided would still pass
                        break
                    if not isinstance(item, dict):
                        raise ValueError(
                            f"Invalid value for attribute '{attr}': {item}"
                        )
                    if get_origin(
                        self.__dataclass_fields__[attr].type
                    ) is Union and type(None) in get_args(
                        self.__dataclass_fields__[attr].type
                    ):
                        child_class = (
                            self.__dataclass_fields__[attr].type.__args__[0].__args__[0]
                        )
                        child_class(**item)
                    else:
                        child_class = self.__dataclass_fields__[attr].type.__args__[0]
                        child_class(**item)
            elif isinstance(value, dict):
                if get_origin(self.__dataclass_fields__[attr].type) is dict:
                    child_class = self.__dataclass_fields__[attr].type.__args__[1]
                    child_class(**list(value.values())[0])
                else:
                    child_class = self.__dataclass_fields__[attr]
                    child_class(**value)
            elif not isinstance(value, self.__dataclass_fields__[attr].type):
                raise ValueError(f"Invalid value for attribute '{attr}': {value}")
