from numbers import Number
from enum import Enum

from api.validator.validators import RequiredType, EnumValidator

class DefaultValueHandling(Enum):
    POPULATE_IF_EMPTY = 0
    POPULATE_IF_NOT_EXISTS = 1
    POPULATE_ALWAYS = 2

class Field(object):
    def __init__(self, name=None, validators=None, default_value=None, 
        default_value_handling=DefaultValueHandling.POPULATE_IF_EMPTY):

        self.name = name
        self.validators = validators if validators else []
        self.default_value = default_value
        self.default_value_handling = default_value_handling

    def convert_value(self, value):
        return value

    def resolve_value(self, value, exists):
        if self.default_value_handling == DefaultValueHandling.POPULATE_ALWAYS:
            return self.default_value
        
        if self.default_value_handling == DefaultValueHandling.POPULATE_IF_NOT_EXISTS and not exists:
            return self.default_value

        if self.default_value_handling == DefaultValueHandling.POPULATE_IF_EMPTY and value == None:
            return self.default_value

        return self.convert_value(value)

    def validate(self, value, exists):
        errors = []
        if not self.validators: return True, []
        for v in self.validators:
            valid, error = v.validate(value, exists)
            if valid or not error: continue
            errors.append(error)

        return len(errors) == 0, errors

class EnumField(Field):
    def __init__(self, enum_type_class, **kwargs):
        super().__init__(**kwargs)
        self.enum_type_class = enum_type_class
        self.validators.append(EnumValidator(enum_type_class))

    def convert_value(self, value):
        try:
            return self.enum_type_class(value)
        except:
            return None

class TypeField(Field):
    def __init__(self, type_class, **kwargs):
        super().__init__(**kwargs)
        self.validators.append(RequiredType(type_class))

class StringField(TypeField):
    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)

class BooleanField(TypeField):
    def __init__(self, **kwargs):
        super().__init__(bool, **kwargs)

class NumberField(TypeField):
    def __init__(self, **kwargs):
        super().__init__(Number, **kwargs)

class IntegerField(TypeField):
    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)

class FloatField(TypeField):
    def __init__(self, **kwargs):
        super().__init__(float, **kwargs)