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


def step_group_name(step_name: str) -> str:
    """Name of the HDF5 group that holds a step."""
    return f"{STEP_GROUP_PREFIX}{step_name}"


def processing_store_path(acquisition_file: str) -> str:
    """
    Where the computed steps of an acquisition live.

    Today the acquisition's own .h5 holds them (the acquisition calls the post-processing on its file).
    The single place to change when the steps move to a file of their own.
    """
    return acquisition_file
