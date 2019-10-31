
class CloudInitException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SshRemoteCommandException(Exception):
    def __init__(self, message):
        super().__init__(message)


class MagmaRequestException(Exception):
    def __init__(self, message):
        super().__init__(message)
