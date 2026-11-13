"""Refused promise: an object measurement names its object, a reference or background has none (see measured_object_role_mismatch_error_intention.md)."""


class MeasuredObjectRoleMismatchError(ValueError):
    def __init__(self, role, measured_object_id):
        if measured_object_id is None:
            message = f"a {role.value} frequency sweep needs the measured object"
        else:
            message = f"a {role.value} frequency sweep has no measured object (got {measured_object_id!r})"
        super().__init__(message)
        self.role = role
        self.measured_object_id = measured_object_id
