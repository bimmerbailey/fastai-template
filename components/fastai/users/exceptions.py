class UserError(Exception):
    pass


class UserInvalidCredentials(UserError):
    pass


class UserLockedError(UserError):
    pass


class UserStatusError(UserError):
    pass


class UserLoginFailed(UserError):
    pass


class UserNotFoundError(UserError):
    pass


class UserInactiveError(UserError):
    pass
