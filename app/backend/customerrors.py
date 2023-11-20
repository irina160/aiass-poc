class AuthError(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class NotInJsonFormatError(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class NotAValidSetError(Exception):
    def __init__(self, message):
        self.error = message


class NotAValidPostRequest(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class NotAValidInstance(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class NotFoundError(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class WrongFileTypeException(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class InternalServerError(Exception):
    def __init__(self, message, code):
        self.error = message
        self.status_code = code


class ConversationNotFoundError(Exception):
    ...
