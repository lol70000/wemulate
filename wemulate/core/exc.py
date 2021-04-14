class WEmulateError(Exception):
    """Generic errors."""

    pass


class WEmulateValidationError(WEmulateError):
    def __init__(self, message="A validation error occured"):
        self.message = message
        super().__init__(self.message)


class WEmulateExecutionError(WEmulateError):
    def __init__(self, message="An execution error occured"):
        self.message = message
        super().__init__(self.message)