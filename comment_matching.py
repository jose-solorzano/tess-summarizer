#
# Helper functions for matching common patterns in TOI Public Comments
#

import re

EB_REGEX = re.compile(r".*\beb\b.*", re.IGNORECASE)
VSHAPED_REGEX = re.compile(r".*\bv[\s-]shaped\b.*", re.IGNORECASE)
VARIABLE_REGEX = re.compile(r".*\b(variable|variability)\b.*", re.IGNORECASE)
ODDEVEN_REGEX = re.compile(r".*\bodd[\s/-]even\b.*", re.IGNORECASE)
SHOULDERS_REGEX = re.compile(r".*\bshoulders?\b.*\bingress\b.*", re.IGNORECASE)


def is_eb(comment: str):
    return EB_REGEX.match(comment) is not None


def is_vshaped(comment: str):
    return VSHAPED_REGEX.match(comment) is not None


def is_variable(comment: str):
    return VARIABLE_REGEX.match(comment) is not None


def is_oddeven(comment: str):
    return ODDEVEN_REGEX.match(comment) is not None


def is_shoulders(comment: str):
    return SHOULDERS_REGEX.match(comment) is not None
