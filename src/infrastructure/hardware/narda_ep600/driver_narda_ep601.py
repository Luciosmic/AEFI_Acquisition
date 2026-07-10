"""Driver bas-niveau pour la sonde Narda EP-601 (protocole série #AAQcommande(params)*, 9600-8N1).
Protocole documenté et validé sur banc dans le sous-projet Ressources/ExperimentalData_ASSOCE/Narda-electric-field-probe-acquisition
(voir notes-narda-electric-field-probe-acquisition/sources/narda-ep60x_protocole-communication.md).
"""
import statistics
import struct

import serial

__version__ = "0.3.0"

AUTO_OFF_DEFAULT_S = 180  # cf. narda-ep60x_protocole-communication.md — reglable via #00en*


class NardaProbeTimeout(TimeoutError):
    """La sonde n'a pas repondu — probablement eteinte (auto-off) ou deconnectee."""


class NardaEP601:
    """Communication série avec la sonde Narda EP-601 via le convertisseur 8053-OC. Adresse broadcast "00"."""

    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def connect(self):
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def disconnect(self):
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc_info):
        self.disconnect()

    def _query(self, cmd, nbytes):
        if self._serial is None:
            raise RuntimeError("not connected — call connect() or use as a context manager")
        self._serial.reset_input_buffer()
        self._serial.write(cmd.encode("ascii"))
        raw = self._serial.read(nbytes)
        if raw == b"":
            raise NardaProbeTimeout(
                f"pas de reponse a {cmd!r} sur {self.port} — sonde probablement eteinte "
                f"(auto-off par defaut apres {AUTO_OFF_DEFAULT_S}s d'inactivite) ou deconnectee"
            )
        return raw

    def get_version(self):
        """Version firmware (#00?v*), ex. "vEP600:1.32 07/20;"."""
        raw = self._query("#00?v*", 32)
        return raw.decode("ascii", "ignore").strip("\x00 ")

    def get_serial_number(self):
        """Numéro de série (#00?s*)."""
        raw = self._query("#00?s*", 32)
        return raw.decode("ascii", "ignore").strip("\x00 ")

    def get_battery_voltage(self):
        """Tension batterie en V (#00?b*)."""
        raw = self._query("#00?b*", 3)
        if len(raw) != 3 or raw[0:1] != b"b":
            raise IOError(f"reponse ?b inattendue: {raw!r}")
        nn = struct.unpack(">H", raw[1:3])[0]
        return 3 * (nn / 1024 * 1.6)

    def get_total_field(self):
        """Champ total isotrope en V/m (#00?T*  — la sonde renvoie le carré, racine prise ici)."""
        raw = self._query("#00?T*", 5)
        if len(raw) != 5 or raw[0:1] != b"T":
            raise IOError(f"reponse ?T inattendue: {raw!r}")
        ff = struct.unpack("<f", raw[1:5])[0]
        return ff**0.5

    def get_field_components(self):
        """Champ par axe (X, Y, Z) en V/m, directement (#00?A*)."""
        raw = self._query("#00?A*", 13)
        if len(raw) != 13 or raw[0:1] != b"A":
            raise IOError(f"reponse ?A inattendue: {raw!r}")
        return struct.unpack("<3f", raw[1:13])

    def set_frequency_correction(self, freq_hz):
        """Active la correction de calibration factory a freq_hz (resolution 10kHz, #00k*).
        Retourne la frequence effectivement appliquee en Hz. La sonde ignore silencieusement
        une frequence hors plage (pas d'erreur explicite) : on le detecte en comparant la
        reponse (echo en MHz, confirme empiriquement) a la demande et on leve ValueError."""
        fr = round(freq_hz / 10_000)
        raw = self._query(f"#00k {fr}*", 5)
        if len(raw) != 5 or raw[0:1] != b"k":
            raise IOError(f"reponse k inattendue: {raw!r}")
        applied_hz = round(struct.unpack("<f", raw[1:5])[0] * 1e6)
        if abs(applied_hz - freq_hz) > 10_000:
            raise ValueError(f"correction non appliquee a {freq_hz} Hz (sonde a repondu {applied_hz} Hz — hors plage ?)")
        return applied_hz

    def get_total_field_averaged(self, n=16):
        """Moyenne arithmetique de n lectures ?T — la sonde n'a pas de moyennage cote protocole
        serie (le mode "Average" du logiciel WinEP600 n'existe que cote GUI/DLL), donc on le
        reproduit ici cote client. n=16 correspond au reglage par defaut de WinEP600."""
        return statistics.fmean(self.get_total_field() for _ in range(n))

    def get_field_components_averaged(self, n=16):
        """Moyenne arithmetique de n lectures ?A, axe par axe. Voir get_total_field_averaged."""
        xs, ys, zs = zip(*(self.get_field_components() for _ in range(n)))
        return statistics.fmean(xs), statistics.fmean(ys), statistics.fmean(zs)


def demo(port):
    print(f"driver_narda_ep601 v{__version__}")
    try:
        with NardaEP601(port) as probe:
            assert probe.get_version().startswith("vEP600")
            x, y, z = probe.get_field_components()
            norm = (x**2 + y**2 + z**2) ** 0.5
            total = probe.get_total_field()
            assert abs(norm - total) < 5.0, f"?A norme={norm:.3f} vs ?T={total:.3f} — écart suspect"
            print("OK —", probe.get_version(), probe.get_serial_number())
            print(f"batterie={probe.get_battery_voltage():.2f}V  X={x:.3f} Y={y:.3f} Z={z:.3f}  |norme|={norm:.3f} V/m  ?T={total:.3f} V/m")

            avg_total = probe.get_total_field_averaged(n=4)
            avg_x, avg_y, avg_z = probe.get_field_components_averaged(n=4)
            print(f"?T moyenne (n=4)={avg_total:.3f} V/m  ?A moyenne (n=4): X={avg_x:.3f} Y={avg_y:.3f} Z={avg_z:.3f}")
    except NardaProbeTimeout as e:
        print(f"TIMEOUT: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    import sys

    demo(sys.argv[1] if len(sys.argv) > 1 else "COM8")
