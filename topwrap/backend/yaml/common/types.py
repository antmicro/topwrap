import marshmallow_dataclass

from topwrap.common_serdes import MarshmallowDataclassExtensions

StrOrInt = str | int
YamlDimension = tuple[StrOrInt, StrOrInt]
YamlBounds = YamlDimension | tuple[YamlDimension, ...]


@marshmallow_dataclass.dataclass(frozen=True)
class ComplexParameter(MarshmallowDataclassExtensions):
    value: int | str
    width: int
