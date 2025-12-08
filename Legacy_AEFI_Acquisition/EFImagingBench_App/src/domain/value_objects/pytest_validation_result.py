"""Tests for ValidationResult value object."""
import pytest
from .validation_result import ValidationResult

def test_validation_result_success():
    """Test creating a successful validation result."""
    result = ValidationResult.success()
    
    assert result.is_valid
    assert len(result.errors) == 0
    assert len(result.warnings) == 0

def test_validation_result_success_with_warnings():
    """Test successful validation with warnings."""
    result = ValidationResult.success(warnings=["Warning 1", "Warning 2"])
    
    assert result.is_valid
    assert len(result.errors) == 0
    assert len(result.warnings) == 2

def test_validation_result_failure():
    """Test creating a failed validation result."""
    result = ValidationResult.failure(errors=["Error 1", "Error 2"])
    
    assert not result.is_valid
    assert len(result.errors) == 2
    assert len(result.warnings) == 0

def test_validation_result_failure_with_warnings():
    """Test failed validation with warnings."""
    result = ValidationResult.failure(
        errors=["Error 1"],
        warnings=["Warning 1"]
    )
    
    assert not result.is_valid
    assert len(result.errors) == 1
    assert len(result.warnings) == 1

def test_validation_result_failure_requires_errors():
    """Test that failure must have at least one error."""
    with pytest.raises(ValueError, match="Failure must have at least one error"):
        ValidationResult.failure(errors=[])

def test_validation_result_immutable():
    """Test that validation result is immutable."""
    result = ValidationResult.success()
    
    with pytest.raises(AttributeError):
        result.is_valid = False

def test_validation_result_boolean_context_true():
    """Test using ValidationResult in boolean context (success)."""
    result = ValidationResult.success()
    
    assert bool(result) is True
    assert result  # Direct boolean evaluation

def test_validation_result_boolean_context_false():
    """Test using ValidationResult in boolean context (failure)."""
    result = ValidationResult.failure(errors=["Error"])
    
    assert bool(result) is False
    assert not result  # Direct boolean evaluation

def test_validation_result_direct_creation():
    """Test creating ValidationResult directly."""
    result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=["Warning"]
    )
    
    assert result.is_valid
    assert len(result.warnings) == 1

