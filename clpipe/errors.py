"""
A module for housing all clpipe-specific Errors.
"""


class NoSubjectTaskFoundError(ValueError):
    pass


class NoImagesFoundError(ValueError):
    pass


class NoSubjectsFoundError(ValueError):
    pass


class SubjectNotFoundError(ValueError):
    pass


class ConfoundsNotFoundError(FileNotFoundError):
    pass


class EVFileNotFoundError(FileNotFoundError):
    pass


class MixingFileNotFoundError(FileNotFoundError):
    pass


class NoiseFileNotFoundError(FileNotFoundError):
    pass


class ImplementationNotFoundError(ValueError):
    pass

class FSFFileNotFoundError(FileNotFoundError):
    pass

class ModelNotFoundError(ValueError):
    pass