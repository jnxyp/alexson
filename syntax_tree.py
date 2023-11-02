from typing import List, Dict, Union, Tuple, Optional
from ast import literal_eval
from abc import ABC
from lexer import Token, TokenType


class AlexsonNode(ABC):
    def __init__(self):
        pass

    def to_alexson(self) -> str:
        raise NotImplementedError()

    def __str__(self):
        return self.to_alexson()

    def __repr__(self):
        return self.to_alexson()


class BlockNode(AlexsonNode, ABC):
    def __init__(self):
        super().__init__()
        self.children: List[AlexsonNode] = []

    def __eq__(self, other):
        return (self.__class__ == other.__class__) and (self.children == other.children)

    def __hash__(self):
        return hash((tuple(self.children), self.__class__))

    def to_alexson(self) -> str:
        return ''.join([child.to_alexson() for child in self.children])

    def is_array(self) -> bool:
        raise NotImplementedError()

    def is_object(self) -> bool:
        raise NotImplementedError()


class Root(BlockNode):
    def __init__(self):
        super().__init__()
        self.primary_obj: Optional[Object, Array] = None

    def get_primary_obj(self) -> Union['Object', 'Array']:
        if self.primary_obj is None:
            for child in self.children:
                if isinstance(child, BlockNode):
                    self.primary_obj = child
                    break
        return self.primary_obj

    def is_array(self) -> bool:
        return self.get_primary_obj().is_array()

    def is_object(self) -> bool:
        return self.get_primary_obj().is_object()

    def __getitem__(self, item: Union[int, str]) -> AlexsonNode:
        return self.get_primary_obj()[item]

    def __setitem__(self, key: Union[int, str], value: AlexsonNode):
        self.get_primary_obj()[key] = value


class Object(BlockNode):
    def __init__(self, ):
        super().__init__()
        self.dict: Dict[str, Tuple[String, AlexsonNode]] = {}

    def __eq__(self, other):
        return super().__eq__(other) and (self.dict == other.dict)

    def __hash__(self):
        return hash((super().__hash__(), tuple(self.dict.items())))

    def __getitem__(self, item: str) -> AlexsonNode:
        return self.dict[item][1]

    def __setitem__(self, key: str, value: AlexsonNode):
        if key in self.dict:
            self.children[self.children.index(self.dict[key][1])] = value
            self.dict[key] = (self.dict[key][0], value)
        else:
            raise NotImplementedError("Cannot add new key to object yet...")


class Array(BlockNode):
    def __init__(self):
        super().__init__()
        self.items: List[AlexsonNode] = []

    def __eq__(self, other):
        return super().__eq__(other) and (self.items == other.items)

    def __hash__(self):
        return hash((super().__hash__(), tuple(self.items)))

    def __getitem__(self, item: int) -> AlexsonNode:
        return self.items[item]

    def __setitem__(self, key: int, value: AlexsonNode):
        self.items[key] = value


class Literal(AlexsonNode, ABC):
    def __init__(self):
        super().__init__()

    def get_value(self) -> Union[str, float, bool, None]:
        raise NotImplementedError()

    def set_value(self, value: Union[str, float, bool, None]):
        raise NotImplementedError()

    def __eq__(self, other):
        return ((self.__class__ is other.__class__) and
                (self.get_value() == other.get_value()) and
                (type(self.get_value()) is type(other.get_value())))

    def __hash__(self):
        return hash((self.get_value(), type(self.get_value()), self.__class__))


class NonEditable(AlexsonNode, ABC):
    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        return self.__class__ is other.__class__

    def __hash__(self):
        return hash(self.__class__)


class String(Literal):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def get_value(self) -> str:
        return self.value

    def set_value(self, value: str):
        self.value = value

    def to_alexson(self) -> str:
        escaped = self.value.replace('"', '\\"')
        return f'"{escaped}"'


class Number(Literal):
    def __init__(self, value: Union[str, float]):
        super().__init__()
        self.value: float = float(value)
        self.original_value: str = str(value)

    def get_value(self) -> float:
        return self.value

    def set_value(self, value: Union[str, float]):
        self.value: float = float(value)
        self.original_value: str = str(value)

    def __eq__(self, other):
        return ((self.__class__ is other.__class__) and
                (type(self.get_value()) is type(other.get_value()))) and \
            (abs(self.get_value() - other.get_value()) < 1e-6)

    def to_alexson(self) -> str:
        return self.original_value


class Variable(Literal):
    def __init__(self, name: str):
        super().__init__()
        self.value: str = name

    def get_value(self) -> str:
        return self.value

    def set_value(self, value: str):
        self.value = value

    def to_alexson(self) -> str:
        return self.value


class Boolean(Literal):
    def __init__(self, boolean: bool):
        super().__init__()
        self.value: bool = boolean

    def get_value(self) -> bool:
        return self.value

    def set_value(self, value: bool):
        self.value = value

    def to_alexson(self) -> str:
        return 'true' if self.value else 'false'


class Null(Literal):
    def __init__(self):
        super().__init__()

    def get_value(self) -> None:
        return None

    def set_value(self, value: None):
        pass

    def to_alexson(self) -> str:
        return 'null'


class NonJson(NonEditable, ABC):
    pass


class Comment(NonJson):
    def __init__(self, comment: str):
        super().__init__()
        self.comment: str = comment

    def __eq__(self, other):
        return super().__eq__(other) and (self.comment == other.comment)

    def __hash__(self):
        return hash((super().__hash__(), self.comment))

    def to_alexson(self) -> str:
        return self.comment


class WhiteSpace(NonJson):
    def to_alexson(self) -> str:
        return ' '


class NewLine(NonJson):
    def to_alexson(self) -> str:
        return '\n'


class Tab(NonJson):
    def to_alexson(self) -> str:
        return '\t'


class Colon(NonEditable):
    def to_alexson(self) -> str:
        return ':'


class Comma(NonEditable):
    def to_alexson(self) -> str:
        return ','


class LBrace(NonEditable):
    def to_alexson(self) -> str:
        return '{'


class RBrace(NonEditable):
    def to_alexson(self) -> str:
        return '}'


class LBracket(NonEditable):
    def to_alexson(self) -> str:
        return '['


class RBracket(NonEditable):
    def to_alexson(self) -> str:
        return ']'
