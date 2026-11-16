import logging

from application.closing_guard_service._tests.system_session_guard_contract_test import SystemSessionGuardContract
from infrastructure.null_system_session_guard.null_system_session_guard import NullSystemSessionGuard


class TestNullSystemSessionGuardContract(SystemSessionGuardContract):
    def make_guard(self) -> NullSystemSessionGuard:
        return NullSystemSessionGuard()


def test_retenir_logue_que_la_garde_n_est_pas_prise_en_charge(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="infrastructure.null_system_session_guard.null_system_session_guard"):
        NullSystemSessionGuard().hold("Acquisition AEFI en cours")
    assert "not supported on this system" in caplog.text
    assert "Acquisition AEFI en cours" in caplog.text
