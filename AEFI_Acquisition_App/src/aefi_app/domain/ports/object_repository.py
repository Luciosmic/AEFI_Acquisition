from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.experiment_object import ExperimentObject, ObjectId

class ObjectRepository(ABC):
    """Port (Interface) for accessing the Object Database.
    
    This allows the Domain Layer to retrieve information about the physical
    objects being studied without knowing the storage mechanism (SQL, JSON, API).
    """

    @abstractmethod
    def get_by_id(self, object_id: ObjectId) -> Optional[ExperimentObject]:
        """Retrieve an object by its unique ID."""
        pass

    @abstractmethod
    def search_by_name(self, name_pattern: str) -> List[ExperimentObject]:
        """Search for objects by name."""
        pass
    
    # Note: No 'save' or 'delete' methods here if this context is Read-Only
    # regarding the Object Database.
