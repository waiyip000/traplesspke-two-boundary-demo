"""Admission of exchanged records; no verdict is accepted from an input report."""
import math
import re

from .files import DemoError, fields


def hex_id(value, size=64):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{%d}" % size, value) is None:
        raise DemoError("Invalid record identifier")
    return value


def prediction(value):
    if value is not None and (type(value) is not int or value not in (0, 1)):
        raise DemoError("Prediction must be the integer 0, integer 1, or null")
    return value


def timestamp(value):
    if type(value) not in (int, float) or not 0 <= value <= 1e12 or not math.isfinite(value):
        raise DemoError("Invalid timestamp")


def submission(value, challenge, challenge_digest):
    fields(value, ("format", "trial_id", "bundle_sha256", "challenge_sha256",
                   "prediction", "method", "recorded_unix"))
    if value["format"] != "trapless-demo-submission-2":
        raise DemoError("Unsupported submission format")
    if value["trial_id"] != challenge["trial_id"] or value["bundle_sha256"] != challenge["bundle_sha256"] or value["challenge_sha256"] != challenge_digest:
        raise DemoError("Submission belongs to a different challenge")
    prediction(value["prediction"])
    if not isinstance(value["method"], str) or not 1 <= len(value["method"]) <= 4096:
        raise DemoError("Invalid method description")
    timestamp(value["recorded_unix"])
    return value
