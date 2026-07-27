"""Driver bas-niveau pour la sonde Narda EP-601 (protocole série #AAQcommande(params)*, 9600-8N1).
Protocole documenté et validé sur banc dans le sous-projet Ressources/ExperimentalData_ASSOCE/Narda-electric-field-probe-acquisition
(voir notes-narda-electric-field-probe-acquisition/sources/narda-ep60x_protocole-communication.md).
"""
import statistics
import struct
import time
from collections import namedtuple

import serial

__version__ = "0.6.0"

AUTO_OFF_DEFAULT_S = 180  # cf. narda-ep60x_protocole-communication.md — reglable via #00en*

# La sonde est un detecteur a diode (antenne + diode par axe), pas un digitaliseur RF :
# elle demodule le champ en une tension proportionnelle a l'amplitude, puis mesure CETTE
# tension. Deux bandes passantes distinctes, a ne pas confondre :
#
#   champ RF (RF_SENSING_RANGE_HZ)  -->  diode/detecteur  -->  amplitude demodulee
#       -->  filtre F1-F8 (READING_BANDWIDTH_HZ_RANGE)  -->  valeur numerique (?T/?A)
#
# RF_SENSING_RANGE_HZ = frequences RF que la sonde peut DETECTER (10kHz-9.25GHz).
# READING_*_RANGE = a quelle vitesse la VALEUR LUE peut suivre un champ qui varie dans le
# temps (scan, modulation...) — sans rapport avec la frequence RF elle-meme.
RF_SENSING_RANGE_HZ = (10_000, 9_250_000_000)  # EP-601, specs datasheet/manuel table 1-2

# Bornes globales connues (datasheet EP600-FEN-20913) ; pas de valeur exacte par filtre F1-F8
# publiee (le manuel renvoie a un document separe absent de docs/). F1 ~ borne haute (rapide),
# F8 ~ borne basse (lent). Voir FILTERS ci-dessous pour les compromis qualitatifs par filtre.
READING_BANDWIDTH_HZ_RANGE = (2.3, 28.0)
READING_RATE_S_RANGE = (0.03, 22.0)

FilterProfile = namedtuple("FilterProfile", "settling_time power_consumption sensitivity mains_rejection")

# Transcription best-effort de la table qualitative du manuel (§5.5.10.1, mise en page PDF
# imparfaite a l'extraction) — voir narda-ep60x_protocole-communication.md. F4-F5 recommandes
# par Narda comme compromis "normal operation".
FILTERS = {
    1: FilterProfile("tres rapide", "tres faible", "faible", "aucune"),
    2: FilterProfile("tres rapide", "tres faible", "moyenne", "faible / elevee"),
    3: FilterProfile("rapide", "faible", "bonne", "correcte"),
    4: FilterProfile("moyen", "moyenne", "elevee", "bonne / elevee"),
    5: FilterProfile("moyen", "moyenne", "elevee", "elevee"),
    6: FilterProfile("moyen", "moyenne", "elevee", "tres elevee"),
    7: FilterProfile("lent", "elevee", "tres elevee", "bonne"),
    8: FilterProfile("lent", "tres elevee", "tres elevee", "elevee"),
}
RECOMMENDED_FILTER = 4


class NardaProbeTimeout(TimeoutError):
    """La sonde n'a pas repondu — probablement eteinte (auto-off) ou deconnectee."""


class NardaEP601:
    """Communication série avec la sonde Narda EP-601 via le convertisseur 8053-OC. Adresse broadcast "00"."""

    def __init__(self, port, baudrate=9600, timeout=1.0, retries=4):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        # Nombre de RE-essais (donc retries=4 => 5 tentatives) sur trame malformee (IOError) —
        # cf. narda-ep60x_protocole-communication.md : le beacon Master (~1/s) peut recouvrir une
        # reponse en cours et la corrompre de facon purement transitoire. NardaProbeTimeout (reponse
        # VIDE) n'est jamais retente ici : ca veut dire sonde eteinte/deconnectee, retenter ne fait
        # que tripler l'attente pour rien — il faut rallumer physiquement (cf.
        # narda-ep60x_allumage-extinction-led.md, aucune commande de reveil a distance).
        self.retries = retries
        self._serial = None
        self._t_connect = None
        # Hook optionnel : callable(dict) appele a CHAQUE echange serie (succes ou echec), pour
        # journaliser en detail sans changer le comportement du driver pour les appelants existants
        # (adapter AEFI_Acquisition notamment). Voir characterize_narda.py pour un exemple d'usage.
        self.on_raw = None

    def connect(self, auto_slave_mode=True):
        """auto_slave_mode=False pour les scripts de diagnostic (characterize_narda.py,
        test_master_slave_mode.py) qui doivent observer l'etat BRUT avant bascule — tout
        code de production (adapter, boucle de polling) doit garder le defaut True."""
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self._t_connect = time.perf_counter()
        if auto_slave_mode:
            self._ensure_slave_mode()

    def _ensure_slave_mode(self):
        """#00?v* est documente comme forcant le passage Master -> Slave (sinon la sonde spam son
        beacon d'identification en continu, cf. narda-ep60x_protocole-communication.md) — mais un
        beacon en cours de transmission peut corrompre CETTE meme trame de bascule. On retente
        avant d'abandonner, pour ne pas laisser silencieusement la sonde en Master."""
        last_error = None
        for _ in range(self.retries + 1):
            try:
                self.get_version()
                return
            except NardaProbeTimeout:
                # reponse VIDE = sonde eteinte/deconnectee, pas un simple recouvrement de trame —
                # retenter ne sert a rien. IMPORTANT: IOError est un ALIAS d'OSError en Python 3 et
                # TimeoutError (donc NardaProbeTimeout) en est une sous-classe — sans ce except
                # explicite AVANT le `except IOError` ci-dessous, ce cas serait silencieusement
                # attrape et retente aussi (bug reel trouve par le self-check de ce module).
                raise
            except IOError as e:
                last_error = e
        raise IOError(
            f"impossible de confirmer le passage en mode Slave apres {self.retries + 1} essais "
            f"(dernier echec: {last_error})"
        )

    def disconnect(self):
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc_info):
        self.disconnect()

    def sniff_idle(self, duration_s=1.0):
        """Ecoute sans envoyer aucune commande pendant duration_s et renvoie les octets recus.
        Toute donnee ici revele un flux non sollicite (mode Master en spam continu, cf.
        narda-ep60x_protocole-communication.md) — normalement la sonde ne doit rien emettre
        sans requete explicite."""
        if self._serial is None:
            raise RuntimeError("not connected — call connect() or use as a context manager")
        t_start = time.perf_counter()
        chunks = []
        while time.perf_counter() - t_start < duration_s:
            n = self._serial.in_waiting
            if n:
                chunks.append(self._serial.read(n))
        return b"".join(chunks)

    def _log_raw(self, cmd, discarded, raw, expected_len, latency_ms):
        """Construit l'evenement de journalisation et le transmet a on_raw (si branche), mais le
        renvoie TOUJOURS : _query s'en sert pour y attacher la valeur decodee apres coup (champ
        "value"), une fois que l'appelant a interprete les octets — _query lui-meme ne connait
        que la commande brute, pas la semantique (V/m, tension...)."""
        t_ref = self._t_connect if self._t_connect is not None else time.perf_counter()
        event = {
            "t_s": round(time.perf_counter() - t_ref, 3),
            "cmd": cmd,
            "discarded_before_hex": discarded.hex(),
            "discarded_before_len": len(discarded),
            "raw_hex": raw.hex(),
            "raw_len": len(raw),
            "expected_len": expected_len,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
            "value": None,
        }
        if self.on_raw is not None:
            self.on_raw(event)
        return event

    def _query(self, cmd, nbytes):
        """Renvoie (raw, event) — event est le meme dict deja transmis a on_raw : l'appelant peut
        y ecrire event["value"] = ... apres decodage pour que la valeur physique apparaisse dans
        le meme journal que les octets bruts (cf. get_total_field et consorts)."""
        if self._serial is None:
            raise RuntimeError("not connected — call connect() or use as a context manager")
        # Remplace reset_input_buffer() par une lecture explicite de ce qui traine : on garde le
        # meme effet (buffer propre avant d'ecrire) mais on peut journaliser ce qui a ete jete —
        # essentiel pour distinguer un flux non sollicite (mode Master) d'un simple decalage de trame.
        n_pending = self._serial.in_waiting
        discarded = self._serial.read(n_pending) if n_pending else b""
        t0 = time.perf_counter()
        self._serial.write(cmd.encode("ascii"))
        raw = self._serial.read(nbytes)
        event = self._log_raw(cmd, discarded, raw, nbytes, (time.perf_counter() - t0) * 1000)
        if raw == b"":
            raise NardaProbeTimeout(
                f"pas de reponse a {cmd!r} sur {self.port} — sonde probablement eteinte "
                f"(auto-off par defaut apres {AUTO_OFF_DEFAULT_S}s d'inactivite) ou deconnectee"
            )
        return raw, event

    def _send_no_reply(self, cmd):
        if self._serial is None:
            raise RuntimeError("not connected — call connect() or use as a context manager")
        n_pending = self._serial.in_waiting
        discarded = self._serial.read(n_pending) if n_pending else b""
        self._serial.write(cmd.encode("ascii"))
        # Purge defensive : observe sur banc le 2026-07-10, la commande suivante recevait des
        # octets residuels apres un #00fn* (echo ? reponse non documentee ?) qui corrompaient
        # sa lecture. On lit/jette tout ce qui traine (bloque jusqu'a self.timeout si rien).
        tail = self._serial.read(64)
        self._log_raw(cmd, discarded, tail, 64, None)

    def _with_retries(self, fn):
        """Retente fn() sur IOError (trame malformee — recouvrement de beacon Master, bruit
        transitoire) jusqu'a self.retries fois. NardaProbeTimeout n'est jamais retente : reponse
        vide = sonde eteinte/deconnectee, retenter ne fait que tripler l'attente pour rien.
        IMPORTANT: IOError est un ALIAS d'OSError en Python 3, et TimeoutError (donc
        NardaProbeTimeout) est une sous-classe d'OSError — sans le `except NardaProbeTimeout: raise`
        AVANT le `except IOError`, ce cas serait silencieusement attrape et retente aussi (bug reel
        trouve par le self-check de ce module, cf. test_driver_raw_log.py)."""
        last_error = None
        for _ in range(self.retries + 1):
            try:
                return fn()
            except NardaProbeTimeout:
                raise
            except IOError as e:
                last_error = e
        raise last_error

    def set_filter(self, filter_number):
        """Regle le filtre de traitement, 1 (F1, rapide/bruite) a 8 (F8, lent/sensible) —
        voir FILTERS[filter_number] pour le compromis (temps de reponse, consommation,
        sensibilite, rejection secteur 50/60Hz) et RECOMMENDED_FILTER pour le defaut Narda.
        Filtre = bande passante de LECTURE (READING_BANDWIDTH_HZ_RANGE), pas la bande RF de
        la sonde (RF_SENSING_RANGE_HZ) — voir le commentaire en tete de module.

        `fn` est en ecriture seule (pas de reponse, pas de commande ?f pour relire l'etat
        courant, table 6-1). Mapping GUI F1-F8 -> index protocole 0-7 INFERE (n∈[0,7]
        documente cote serie, F1-F8 cote WinEP600, jamais confirme explicitement egal par le
        manuel) — a verifier sur banc si le comportement observe ne correspond pas a
        l'attendu."""
        if filter_number not in FILTERS:
            raise ValueError(f"filtre {filter_number} hors plage (1-8)")
        self._send_no_reply(f"#00f{filter_number - 1}*")

    def get_version(self):
        """Version firmware (#00?v*), ex. "vEP600:1.32 07/20;". Retente sur IOError (cf.
        _with_retries) — cette query sert aussi de bascule Master->Slave (_ensure_slave_mode)."""
        def attempt():
            raw, event = self._query("#00?v*", 32)
            text = raw.decode("ascii", "ignore").strip("\x00 ")
            if not text.startswith("v"):
                raise IOError(f"reponse ?v inattendue (probable recouvrement beacon Master): {raw!r}")
            event["value"] = text
            return text
        return self._with_retries(attempt)

    def get_serial_number(self):
        """Numéro de série (#00?s*)."""
        def attempt():
            raw, event = self._query("#00?s*", 32)
            text = raw.decode("ascii", "ignore").strip("\x00 ")
            if not text.startswith("s"):
                raise IOError(f"reponse ?s inattendue: {raw!r}")
            event["value"] = text
            return text
        return self._with_retries(attempt)

    def get_battery_voltage(self):
        """Tension batterie en V (#00?b*)."""
        def attempt():
            raw, event = self._query("#00?b*", 3)
            if len(raw) != 3 or raw[0:1] != b"b":
                raise IOError(f"reponse ?b inattendue: {raw!r}")
            nn = struct.unpack(">H", raw[1:3])[0]
            voltage = 3 * (nn / 1024 * 1.6)
            event["value"] = voltage
            return voltage
        return self._with_retries(attempt)

    def get_total_field(self):
        """Champ total isotrope en V/m (#00?T*  — la sonde renvoie le carré, racine prise ici)."""
        def attempt():
            raw, event = self._query("#00?T*", 5)
            if len(raw) != 5 or raw[0:1] != b"T":
                raise IOError(f"reponse ?T inattendue: {raw!r}")
            ff = struct.unpack("<f", raw[1:5])[0]
            value = ff**0.5
            event["value"] = value
            return value
        return self._with_retries(attempt)

    def get_field_components(self):
        """Champ par axe (X, Y, Z) en V/m, directement (#00?A*)."""
        def attempt():
            raw, event = self._query("#00?A*", 13)
            if len(raw) != 13 or raw[0:1] != b"A":
                raise IOError(f"reponse ?A inattendue: {raw!r}")
            xyz = struct.unpack("<3f", raw[1:13])
            event["value"] = list(xyz)  # tuple -> list, json.dumps ne serialise pas les tuples nativement
            return xyz
        return self._with_retries(attempt)

    def set_auto_off_delay(self, seconds):
        """Regle le delai avant extinction automatique apres la derniere commande RECUE et
        reconnue (#00e <n>*, confirme dans le manuel — pas le trafic du beacon Master, cf.
        narda-ep60x_protocole-communication.md). Max 10800s (3h). Non permanent : revient a
        AUTO_OFF_DEFAULT_S a chaque power-on. Renvoie True si accepte, False si hors plage
        (defaut 180s repris silencieusement par la sonde)."""
        raw, event = self._query(f"#00e {int(seconds)}*", 1)
        accepted = raw == b"e"
        event["value"] = accepted
        return accepted

    def set_frequency_correction(self, freq_hz):
        """Active la correction de calibration factory a freq_hz (resolution 10kHz, #00k*).
        Retourne la frequence effectivement appliquee en Hz. La sonde ignore silencieusement
        une frequence hors plage (pas d'erreur explicite) : on le detecte en comparant la
        reponse (echo en MHz, confirme empiriquement) a la demande et on leve ValueError."""
        fr = round(freq_hz / 10_000)
        raw, event = self._query(f"#00k {fr}*", 5)
        if len(raw) != 5 or raw[0:1] != b"k":
            raise IOError(f"reponse k inattendue: {raw!r}")
        applied_hz = round(struct.unpack("<f", raw[1:5])[0] * 1e6)
        event["value"] = applied_hz
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
