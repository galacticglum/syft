from functools import wraps
from flask import request, g
from api.http_errors import BadContentTypeError, InvalidDataError

from api.validator.fields import Field

def require_json_content_type(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            raise BadContentTypeError('application/json')
        
        return func(*args, **kwargs)
    return wrapper

def validate_route(schema_type):
    def decorator(func):
        @require_json_content_type
        @wraps(func)
        def wrapper(*args, **kwargs):
            validator_schema = schema_type(request.get_json())
            valid, errors = validator_schema.validate()
            if not valid:
                raise InvalidDataError(**errors)
            
            g.validator_data = validator_schema.get_values()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_validator_data():
    return getattr(g, 'validator_data', None)

class Schema(object):
    def __init__(self, data):
        self.data = data

    def _resolve_field_value(self, field, field_name):
        exists = field_name in self.data
        return field.resolve_value(None if not exists else self.data[field_name], exists)

    def validate(self):
        fields = self._get_fields()
        errors = {}
        for field_name, field in fields.items():
            value = self._resolve_field_value(field, field_name)
            exists = field_name in self.data
            valid, error = field.validate(value, exists)
            
            if valid: continue
            errors[field_name] = error

        return len(errors) == 0, errors

    def get_values(self):
        fields = self._get_fields()
        return {field_name:self._resolve_field_value(field, field_name) for field_name,field in fields.items()}

    def _get_fields(self):
        v = dir(self.__class__)
        fields = {}
        for field_name in v:
            instance = getattr(self, field_name)
            if not isinstance(instance, Field): continue

            if instance.name == None:
                fields[field_name] = instance
            else:
                fields[instance.name] = instance

        return fields