from application.closing_guard_service._tests.system_session_guard_contract_test import SystemSessionGuardContract
from infrastructure.null_system_session_guard.fake.fake_null_system_session_guard import FakeNullSystemSessionGuard


class TestFakeNullSystemSessionGuardContract(SystemSessionGuardContract):
    def make_guard(self) -> FakeNullSystemSessionGuard:
        return FakeNullSystemSessionGuard()


def test_le_faux_retient_les_raisons_et_l_etat() -> None:
    guard = FakeNullSystemSessionGuard()
    guard.hold("Acquisition AEFI en cours")
    assert guard.holds == ["Acquisition AEFI en cours"]
    assert guard.is_holding
    guard.release()
    assert guard.releases == 1
    assert not guard.is_holding


def test_le_faux_ne_compte_pas_un_relachement_sans_retenue() -> None:
    guard = FakeNullSystemSessionGuard()
    guard.release()
    assert guard.releases == 0
