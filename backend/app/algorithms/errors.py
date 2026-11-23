"""Exception types raised by the algorithm layer.

The algorithm modules are framework independent: they raise these plain
exceptions and the API layer translates them into HTTP responses.
"""

from __future__ import annotations


class AlgorithmError(ValueError):
    """Base class for invalid input handed to an algorithm."""


class NegativeWeightError(AlgorithmError):
    """A road (edge) was given a negative or non-finite weight."""


class UnknownNodeError(AlgorithmError):
    """A location that is not part of the graph was referenced."""


class ResourceLimitError(AlgorithmError):
    """The requested problem would need more memory than the safety limit."""
