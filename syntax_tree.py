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
        return isinstance(self, Array)

    def is_object(self) -> bool:
        return isinstance(self, Object)

    def to_dict_or_array(self) -> Union[Dict, List]:
        if isinstance(self, Root):
            return self.get_primary_obj().to_dict_or_array()
        if self.is_array():
            assert isinstance(self, Array)
            return self.to_array()
        else:
            assert isinstance(self, Object)
            return self.to_dict()


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
        return isinstance(self.get_primary_obj(), Array)

    def is_object(self) -> bool:
        return isinstance(self.get_primary_obj(), Object)

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

    def rename_key(self, old_key: str, new_key: str) -> None:
        if old_key not in self.dict:
            raise KeyError(f'Key {old_key!r} not found in object')
        if new_key in self.dict:
            raise KeyError(f'Key {new_key!r} already exists in object')
        key_node, value_node = self.dict.pop(old_key)
        key_node.value = new_key
        self.dict[new_key] = (key_node, value_node)

    def to_dict(self) -> Dict:
        d = {}
        for key, (key_node, value_node) in self.dict.items():
            if isinstance(value_node, Literal):
                d[key] = value_node.get_value()
            elif isinstance(value_node, Object):
                d[key] = value_node.to_dict()
            elif isinstance(value_node, Array):
                d[key] = value_node.to_array()
            else:
                raise NotImplementedError()
        return d

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

    def to_array(self) -> List:
        array = []
        for item in self.items:
            if isinstance(item, Literal):
                array.append(item.get_value())
            elif isinstance(item, Object):
                array.append(item.to_dict())
            elif isinstance(item, Array):
                array.append(item.to_array())
            else:
                raise NotImplementedError()
        return array


class Literal(AlexsonNode, ABC):
    def __init__(self):
        super().__init__()

    def get_value(self) -> Union[str, float, bool, None]:
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
    def __init__(self, value: str, quoted: bool = True):
        super().__init__()
        self.value: str = value
        self.quoted: bool = quoted

    def get_value(self) -> str:
        return self.value

    def to_alexson(self) -> str:
        if not self.quoted:
            return self.value
        escaped = self.value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'


class Number(Literal):
    def __init__(self, value: Union[str, float]):
        super().__init__()
        self.value: float = float(value)
        self.original_value: str = str(value)

    def get_value(self) -> float:
        return self.value

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

    def to_alexson(self) -> str:
        return self.value


class Boolean(Literal):
    def __init__(self, boolean: bool):
        super().__init__()
        self.value: bool = boolean

    def get_value(self) -> bool:
        return self.value

    def to_alexson(self) -> str:
        return 'true' if self.value else 'false'


class Null(Literal):
    def __init__(self):
        super().__init__()

    def get_value(self) -> None:
        return None

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
