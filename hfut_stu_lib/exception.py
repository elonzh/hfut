from __future__ import unicode_literals


class SystemLoginFailed(Exception):
    pass


class IPBanned(SystemLoginFailed):
    pass


class WrongPasswordPattern(Exception):
    pass
