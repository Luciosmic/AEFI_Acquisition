from abc import ABC, abstractmethod

class IMotionControlOutputPort(ABC):
    """
    Output port for motion control updates.
    Implemented by the Presenter to update the View.

    Responsibility:
        - Déclarer les méthodes de présentation liées à la motion : mise à jour de position, retour d'erreur de commande motion.

    Rationale:
        Port de sortie du `MotionControlService` vers la UI pour notifier les changements de position et les erreurs de motion. Évite que le service appelle directement des widgets Qt.

    Design:
        - **Port output** co-localisé dans `motion_control_service/`.
        - Implémenté par `MotionPresenter` dans `interface/presenters/`.
    """
    
    @abstractmethod
    def update_position(self, x: float, y: float) -> None:
        """Update the displayed position."""
        pass

    @abstractmethod
    def update_status(self, is_moving: bool) -> None:
        """Update the motion status (e.g. moving/stopped)."""
        pass

    @abstractmethod
    def present_error(self, message: str) -> None:
        """Present an error message to the user."""
        pass
