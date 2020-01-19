from re import match, IGNORECASE

def resolve_text(singular, plural, value):
    if value == 1 or value == -1: return singular
    return plural

class RequiredType(object):
    def __init__(self, type_class, error_message=None):
        self.type_class = type_class
        self.error_message = error_message

    def validate(self, value, exists):
        if not exists or isinstance(value, self.type_class): return True, ''
        if self.error_message is None:
            self.error_message =  'Expected \'{0}\' type, got \'{1}\' type.'.format(self.type_class.__name__, type(value).__name__)

        return False, self.error_message

class EnumValidator(object):
    def __init__(self, enum_type_class, error_message=None):
        self.enum_type_class = enum_type_class
        self.error_message = error_message
    
    def validate(self, value, exists):
        # The value can either be the direct enum class or the value of one
        # of the members in the enum class.
        if value in self.enum_type_class or any(value == item.value for item in self.enum_type_class):
            return True, ''
        
        if self.error_message is None:
            self.error_message = 'Expected Enum value of type \'{0}\', got invalid value.'.format(self.enum_type_class.__name__)

        return False, self.error_message

class DataRequired(object):
    def __init__(self, error_message=None):
        self.error_message = error_message

    def validate(self, value, exists):
        if exists: return True, ''
        if self.error_message is None:
            self.error_message = 'Field is required.'

        return False, self.error_message

class Length(object):
    def __init__(self, minimum=0, maximum=float('inf'), error_message=None):
        assert minimum <= maximum, '`minimum` cannot be more than `maximum`.'

        self.min = minimum
        self.max = maximum
        self.error_message = error_message

    def validate(self, value, exists):
        if not hasattr(value, '__len__'): return False, 'Value of type \'{0}\' has no \'__len__\' attribute.'.format(type(value).__name__)
        if self.min <= len(value) <= self.max: return True, ''
        
        if self.error_message is None:
            if self.max == float('inf'):
                self.error_message = resolve_text('Field must be at least {0} element long.',
                    'Field must be at least {0} elements long.', self.min).format(self.min)
            elif self.min == 0:
                self.error_message = resolve_text('Field cannot be longer than {0} element.',
                    'Field cannot be longer than {0} elements.', self.max).format(self.max)
            else:
                self.error_message = 'Field must be between {0} and {1} elements long.'.format(self.min, self.max)

        return False, self.error_message

class Pattern(object):
    def __init__(self, regex_pattern, flags=0, error_message=None):
        self.regex_pattern = regex_pattern
        self.error_message = error_message
        self.flags = flags

    def validate(self, value, exists):
        if type(value) != str: return False, 'Expected value of type \'str\' to perform regular expression matching.'
        if match(self.regex_pattern, value, self.flags): return True, ''
        if self.error_message is None:
            self.error_message = 'Failed to match with regular expression pattern.'

        return False, self.error_message

class Email(Pattern):
    EMAIL_PATTERN = r'''^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]
        {1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'''

    def __init__(self, error_message=None):
        super().__init__(self.EMAIL_PATTERN, IGNORECASE, error_message)

    def validate(self, value, exists):
        if self.error_message is None:
            self.error_message = 'Invalid email address.'

        return super().validate(value, exists)