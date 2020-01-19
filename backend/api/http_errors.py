from api.string_utilities import list_join, kwargs_to_list

class BadContentTypeError(Exception):
    """
    Raised when an HTTP request sends an invalid content type.
    """

    code = 415

    def __init__(self, expected_content_type):
        self.description = 'Expected \'Content-Type: {0}\''.format(expected_content_type)
        self.data = None

class InvalidDataError(Exception):
    """
    Raised when data validation fails
    
    """

    code = 400

    def __init__(self, **parameter_info):
        self.description = 'Failed to validate data!'
        self.data = {
            'parameter_info': parameter_info
        }