"""
hdf5_step_format - How the computed steps are laid out in an HDF5 file (see hdf5_step_format_intention.md).
"""

# One group per step, named after the step, at the root of the file.
STEP_GROUP_PREFIX = "/"
DATA_DATASET = "data"

# Attributes of a step group.
TIMESTAMP_ATTR = "timestamp"
STEP_NAME_ATTR = "step_name"
DATA_SHAPE_ATTR = "data_shape"
DATA_DTYPE_ATTR = "data_dtype"

# Attributes of the file root.
PROCESSING_HISTORY_ATTR = "processing_history"
SOURCE_CSV_ATTR = "source_csv"
LOAD_TIMESTAMP_ATTR = "load_timestamp"
SOURCE_SHA256_ATTR = "source_sha256"  # SHA-256 of the CSV that was read
SOURCE_ACTIVITY_ID_ATTR = "source_activity_id"  # provenance.activity.id of the acquisition parameters file
SOURCE_DECLARED_SHA256_ATTR = "source_declared_sha256"  # SHA-256 the acquisition recorded for that CSV (data.files)
SOURCE_SHA256_MATCHES_ATTR = "source_sha256_matches"  # whether the two hashes are equal; absent when none is declared

# The points as read from the CSV: a group beside the steps, never a step.
RAW_SCAN_GROUP = "raw_scan"
RAW_POSITIONS_DATASET = "positions"
RAW_VALUES_DATASET = "values"
RAW_CHANNEL_NAMES_ATTR = "channel_names"


def step_group_name(step_name: str) -> str:
    """Name of the HDF5 group that holds a step."""
    return f"{STEP_GROUP_PREFIX}{step_name}"


def processing_store_path(acquisition_file: str) -> str:
    """
    Where the computed steps of an acquisition live.

    The acquisition's `.h5`, which the post-processing creates (the acquisition exports the CSV only): the steps, the raw
    points re-read from the CSV and their provenance are one file. The single place to change if they split.
    """
    return acquisition_file
