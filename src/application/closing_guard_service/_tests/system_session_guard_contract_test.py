"""Contract suite of ISystemSessionGuard: the promises every implementation keeps (H20).

An implementation's test subclasses SystemSessionGuardContract (pytest collects the `Test…` subclass,
never this base) and gives `make_guard()`.
"""

import threading
from abc import ABC, abstractmethod

import pytest

from application.closing_guard_service.ports.i_system_session_guard import ISystemSessionGuard


class SystemSessionGuardContract(ABC):
    @abstractmethod
    def make_guard(self) -> ISystemSessionGuard:
        """A fresh implementation under test."""

    def test_une_raison_vide_est_refusee(self) -> None:
        guard = self.make_guard()
        with pytest.raises(ValueError):
            guard.hold("")
        with pytest.raises(ValueError):
            guard.hold("   ")

    def test_retenir_puis_relacher_se_fait_sans_erreur(self) -> None:
        guard = self.make_guard()
        guard.hold("Acquisition AEFI en cours")
        guard.release()

    def test_relacher_sans_avoir_retenu_ne_fait_rien(self) -> None:
        self.make_guard().release()

    def test_retenir_et_relacher_depuis_un_autre_fil(self) -> None:
        guard = self.make_guard()
        errors = []

        def cycle() -> None:
            try:
                guard.hold("Acquisition AEFI en cours")
                guard.release()
            except Exception as error:  # the assertion below names it
                errors.append(error)

        worker = threading.Thread(target=cycle)
        worker.start()
        worker.join(timeout=5)
        assert errors == []
