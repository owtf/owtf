"""

.. module:: constants
    :synopsis: Constants used across the PTP library.

.. moduleauthor:: Tao Sauvage

"""


#: :class:`int` Ranking value of an unknown/unranked vulnerability.
UNKNOWN = 0
#: :class:`int` Ranking value of an informational risk vulnerability.
INFO = 1
#: :class:`int` Ranking value of a low risk vulnerability.
LOW = 2
#: :class:`int` Ranking value of a medium risk vulnerability.
MEDIUM = 3
#: :class:`int` Ranking value of a high risk vulnerability.
HIGH = 4

#: :class:`dict` Unified scale of the ranking values.
RANKING_SCALE = {
    HIGH: HIGH, MEDIUM: MEDIUM, LOW: LOW, INFO: INFO, UNKNOWN: UNKNOWN}
