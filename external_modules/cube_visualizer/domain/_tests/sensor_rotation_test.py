"""Tests unitaires pour sensor_rotation (quaternions / Euler)."""
import numpy as np
import pytest

from cube_visualizer.domain.sensor_rotation import (
    euler_xyz_from_quaternion,
    get_default_quaternion,
    get_default_theta_x,
    get_default_theta_y,
    quaternion_from_euler_xyz,
    quaternion_identity,
    quaternion_multiply,
    quaternion_slerp,
    rotation_from_quaternion,
)


class TestQuaternionConversions:
    def test_euler_to_quaternion_identity(self):
        quat = quaternion_from_euler_xyz(0, 0, 0)
        expected = quaternion_identity()
        assert np.allclose(quat, expected, atol=1e-10)

    def test_quaternion_to_euler_identity(self):
        quat = quaternion_identity()
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(quat)
        assert np.allclose([theta_x, theta_y, theta_z], [0, 0, 0], atol=1e-10)

    def test_euler_quaternion_roundtrip(self):
        test_cases = [
            (45.0, 30.0, 60.0),
            (90.0, 0.0, 0.0),
            (0.0, 90.0, 0.0),
            (0.0, 0.0, 90.0),
            (30.0, 45.0, 60.0),
            (-45.0, -30.0, -60.0),
        ]
        for theta_x, theta_y, theta_z in test_cases:
            quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
            theta_x2, theta_y2, theta_z2 = euler_xyz_from_quaternion(quat)
            assert np.allclose(
                [theta_x, theta_y, theta_z],
                [theta_x2, theta_y2, theta_z2],
                atol=1e-8,
            ), f"Roundtrip failed for ({theta_x}, {theta_y}, {theta_z})"

    def test_gimbal_lock_case(self):
        theta_x, theta_y, theta_z = 30.0, 90.0, 45.0
        quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
        norm = np.linalg.norm(quat)
        assert np.isclose(norm, 1.0, atol=1e-10)
        rot = rotation_from_quaternion(quat)
        v = np.array([1, 0, 0])
        v_rotated = rot.apply(v)
        assert not np.allclose(v, v_rotated, atol=1e-6)


class TestQuaternionOperations:
    def test_quaternion_identity_is_neutral(self):
        q = quaternion_from_euler_xyz(45, 30, 60)
        q_id = quaternion_identity()
        assert np.allclose(quaternion_multiply(q, q_id), q, atol=1e-10)
        assert np.allclose(quaternion_multiply(q_id, q), q, atol=1e-10)

    def test_quaternion_multiply_composition(self):
        q_x = quaternion_from_euler_xyz(90, 0, 0)
        q_y = quaternion_from_euler_xyz(0, 90, 0)
        q_composed = quaternion_multiply(q_y, q_x)
        rot_composed = rotation_from_quaternion(q_composed)
        v = np.array([1, 0, 0])
        v_result = rot_composed.apply(v)
        expected = np.array([0, 0, -1])
        assert np.allclose(v_result, expected, atol=1e-10)

    def test_quaternion_norm_preserved(self):
        test_angles = [
            (0, 0, 0),
            (45, 30, 60),
            (90, 90, 90),
            (180, 0, 0),
            (-45, -30, -60),
        ]
        for theta_x, theta_y, theta_z in test_angles:
            quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
            norm = np.linalg.norm(quat)
            assert np.isclose(norm, 1.0, atol=1e-10), (
                f"Quaternion norm != 1 for angles ({theta_x}, {theta_y}, {theta_z})"
            )


class TestQuaternionSlerp:
    def test_slerp_endpoints(self):
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 0, 0)
        assert np.allclose(quaternion_slerp(q1, q2, 0.0), q1, atol=1e-10)
        assert np.allclose(quaternion_slerp(q1, q2, 1.0), q2, atol=1e-10)

    def test_slerp_midpoint(self):
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 0, 0)
        q_mid = quaternion_slerp(q1, q2, 0.5)
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(q_mid)
        assert np.isclose(theta_x, 45.0, atol=1.0)
        assert np.isclose(theta_y, 0.0, atol=1.0)
        assert np.isclose(theta_z, 0.0, atol=1.0)

    def test_slerp_smoothness(self):
        q1 = quaternion_identity()
        q2 = quaternion_from_euler_xyz(90, 45, 30)
        t_values = np.linspace(0, 1, 11)
        quats = [quaternion_slerp(q1, q2, t) for t in t_values]
        for quat in quats:
            assert np.isclose(np.linalg.norm(quat), 1.0, atol=1e-10)
        angles = [euler_xyz_from_quaternion(q) for q in quats]
        for i in range(len(angles) - 1):
            diff = np.array(angles[i + 1]) - np.array(angles[i])
            assert np.all(np.abs(diff) < 20), "Saut brusque détecté dans SLERP"


class TestDefaultQuaternion:
    def test_default_quaternion_matches_default_euler(self):
        q_default = get_default_quaternion()
        theta_x, theta_y, theta_z = euler_xyz_from_quaternion(q_default)
        assert np.isclose(theta_x, get_default_theta_x(), atol=1e-8)
        assert np.isclose(theta_y, get_default_theta_y(), atol=1e-8)
        assert np.isclose(theta_z, 0.0, atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
