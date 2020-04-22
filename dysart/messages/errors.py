import platform


class DysartError(Exception):
    pass


class ValidationError(DysartError):
    pass


class ModuleNotFoundError(DysartError):
    pass


class ServiceError(DysartError):
    pass


class ServiceNotFoundError(ServiceError):
    status = 'fail'
    message = 'service not found.'


class JobError(ServiceError):
    status = 'warn'
    message = 'job failed.'


class AlreadyOnError(ServiceError):
    status = 'fail'
    message = 'already on.'


class MultipleInstancesError(ServiceError):
    status = 'fail'
    message = 'multiple instances found.'


class AlreadyOffError(ServiceError):
    status = 'fail'
    message = 'already off.'


class ConnectionError(ServiceError):
    status = 'warn'
    message = 'cannot connect.'


class UnsupportedPlatformError(DysartError):
    status = 'fail'
    message = 'unsupported platform.'

    def __str__(self):
        return platform.system()
