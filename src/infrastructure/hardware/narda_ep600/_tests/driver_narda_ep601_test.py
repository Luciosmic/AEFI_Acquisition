import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.narda_ep600.driver_narda_ep601 import NardaEP601, NardaProbeTimeout


class TestNardaEP601(unittest.TestCase):
    def setUp(self):
        patcher = patch("infrastructure.hardware.narda_ep600.driver_narda_ep601.serial.Serial")
        self.mock_serial_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_serial = MagicMock()
        self.mock_serial.is_open = True
        # in_waiting doit etre un entier explicite (0), pas le MagicMock par defaut (truthy) —
        # sinon _query() croit qu'il y a des octets residuels a jeter et consomme un item EN
        # TROP de mock_serial.read.side_effect a chaque appel, desynchronisant les listes de
        # side_effect a longueur exacte (cf. tests *_averaged ci-dessous, casses par ce piege
        # lors du passage a v0.6.0 du driver — piege reel trouve en syncant depuis le sous-projet).
        self.mock_serial.in_waiting = 0
        self.mock_serial_cls.return_value = self.mock_serial

        self.probe = NardaEP601("COM8")
        # auto_slave_mode=False : ces tests portent sur le comportement de chaque methode
        # individuellement, pas sur la bascule Master->Slave (cf. TestNardaEP601SlaveModeAndRetries
        # plus bas pour cette derniere).
        self.probe.connect(auto_slave_mode=False)

    def test_connect_opens_serial_with_configured_params(self):
        self.mock_serial_cls.assert_called_once_with("COM8", 9600, timeout=1.0)

    def test_disconnect_closes_serial(self):
        self.probe.disconnect()
        self.mock_serial.close.assert_called_once()
        self.assertIsNone(self.probe._serial)

    def test_context_manager_connects_and_disconnects(self):
        with NardaEP601("COM8") as probe:
            self.assertIsNotNone(probe._serial)
        self.mock_serial.close.assert_called()

    def test_query_raises_timeout_on_empty_response(self):
        self.mock_serial.read.return_value = b""
        with self.assertRaises(NardaProbeTimeout):
            self.probe.get_version()

    def test_get_version_strips_padding(self):
        self.mock_serial.read.return_value = b"vEP600:1.32 07/20;\x00\x00\x00"
        self.assertEqual(self.probe.get_version(), "vEP600:1.32 07/20;")

    def test_get_battery_voltage_conversion(self):
        nn = 700
        self.mock_serial.read.return_value = b"b" + struct.pack(">H", nn)
        expected = 3 * (nn / 1024 * 1.6)
        self.assertAlmostEqual(self.probe.get_battery_voltage(), expected)

    def test_get_total_field_takes_square_root_of_reported_value(self):
        squared = 25.0
        self.mock_serial.read.return_value = b"T" + struct.pack("<f", squared)
        self.assertAlmostEqual(self.probe.get_total_field(), 5.0, places=4)

    def test_get_field_components_unpacks_three_axes(self):
        self.mock_serial.read.return_value = b"A" + struct.pack("<3f", 1.0, 2.0, 3.0)
        x, y, z = self.probe.get_field_components()
        self.assertAlmostEqual(x, 1.0, places=5)
        self.assertAlmostEqual(y, 2.0, places=5)
        self.assertAlmostEqual(z, 3.0, places=5)

    def test_get_total_field_averaged_computes_arithmetic_mean(self):
        squares = [4.0, 9.0, 16.0]
        self.mock_serial.read.side_effect = [b"T" + struct.pack("<f", s) for s in squares]
        avg = self.probe.get_total_field_averaged(n=len(squares))
        expected = sum(s**0.5 for s in squares) / len(squares)
        self.assertAlmostEqual(avg, expected)

    def test_get_field_components_averaged_computes_per_axis_mean(self):
        readings = [(1.0, 2.0, 3.0), (3.0, 4.0, 5.0)]
        self.mock_serial.read.side_effect = [
            b"A" + struct.pack("<3f", *r) for r in readings
        ]
        avg_x, avg_y, avg_z = self.probe.get_field_components_averaged(n=len(readings))
        self.assertAlmostEqual(avg_x, 2.0, places=4)
        self.assertAlmostEqual(avg_y, 3.0, places=4)
        self.assertAlmostEqual(avg_z, 4.0, places=4)


class TestNardaEP601SlaveModeAndRetries(unittest.TestCase):
    """Comportement introduit en v0.6.0 : connect() force le mode Slave par defaut (le beacon
    Master, ~1/s, peut corrompre une reponse en cours — cf. narda-ep60x_protocole-communication.md
    dans le sous-projet Narda), et les getters retentent une trame malformee (IOError) sans jamais
    retenter un NardaProbeTimeout (reponse vide = sonde eteinte, cf.
    narda-ep60x_allumage-extinction-led.md)."""

    def setUp(self):
        patcher = patch("infrastructure.hardware.narda_ep600.driver_narda_ep601.serial.Serial")
        self.mock_serial_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_serial = MagicMock()
        self.mock_serial.is_open = True
        self.mock_serial.in_waiting = 0
        self.mock_serial_cls.return_value = self.mock_serial

    def test_connect_default_forces_slave_mode_via_version_query(self):
        self.mock_serial.read.return_value = b"vEP600:1.32 07/20;"
        probe = NardaEP601("COM8")
        probe.connect()  # auto_slave_mode=True par defaut
        self.mock_serial.write.assert_called_with(b"#00?v*")

    def test_connect_auto_slave_mode_false_sends_no_query(self):
        probe = NardaEP601("COM8")
        probe.connect(auto_slave_mode=False)
        self.mock_serial.write.assert_not_called()

    def test_get_total_field_retries_on_malformed_frame_then_succeeds(self):
        probe = NardaEP601("COM8")
        probe.connect(auto_slave_mode=False)
        good = b"T" + struct.pack("<f", 16.0)
        # 1er octet ne commence pas par 'T' -> simule un fragment de beacon Master qui recouvre
        # la reponse ; le 2e essai (dans le budget self.retries) recoit la bonne trame.
        self.mock_serial.read.side_effect = [b"xxxxx", good]
        self.assertAlmostEqual(probe.get_total_field(), 4.0)

    def test_get_total_field_gives_up_after_exhausting_retry_budget(self):
        probe = NardaEP601("COM8", retries=2)
        probe.connect(auto_slave_mode=False)
        self.mock_serial.read.return_value = b"xxxxx"  # jamais valide, quel que soit le nombre d'essais
        with self.assertRaises(IOError):
            probe.get_total_field()
        # retries=2 => 3 tentatives, une seule lecture par tentative (in_waiting=0 -> pas de purge)
        self.assertEqual(self.mock_serial.read.call_count, 3)

    def test_probe_timeout_is_never_retried(self):
        probe = NardaEP601("COM8", retries=4)
        probe.connect(auto_slave_mode=False)
        self.mock_serial.read.return_value = b""  # reponse vide = sonde eteinte
        with self.assertRaises(NardaProbeTimeout):
            probe.get_total_field()
        # PAS de retry sur NardaProbeTimeout, malgre retries=4 : une seule tentative.
        # IMPORTANT: IOError est un alias d'OSError et TimeoutError (donc NardaProbeTimeout) en
        # est une sous-classe en Python 3 — sans un `except NardaProbeTimeout: raise` explicite
        # AVANT le `except IOError` dans le driver, ce cas serait silencieusement retente aussi.
        self.assertEqual(self.mock_serial.read.call_count, 1)

    def test_on_raw_hook_receives_decoded_value_alongside_raw_bytes(self):
        probe = NardaEP601("COM8")
        probe.connect(auto_slave_mode=False)
        events = []
        probe.on_raw = events.append
        self.mock_serial.read.return_value = b"T" + struct.pack("<f", 16.0)

        value = probe.get_total_field()

        self.assertEqual(value, 4.0)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["value"], 4.0)
        self.assertEqual(events[0]["cmd"], "#00?T*")


if __name__ == "__main__":
    unittest.main()
