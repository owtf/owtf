"""
owtf.constants
~~~~~~~~~~~~~~

Ranking constants used across the framework.
"""

# `int` value of ranks
OWTF_UNRANKED = -1
OWTF_PASSING = 0
OWTF_INFO = 1
OWTF_LOW = 2
OWTF_MEDIUM = 3
OWTF_HIGH = 4
OWTF_CRITICAL = 5

# Maps `int` value of ranks with `string` value.
RANKS = {
    OWTF_UNRANKED: 'Unranked',
    OWTF_PASSING: 'Passing',
    OWTF_INFO: 'Informational',
    OWTF_LOW: 'Low',
    OWTF_MEDIUM: 'Medium',
    OWTF_HIGH: 'High',
    OWTF_CRITICAL: 'Critical',
}
