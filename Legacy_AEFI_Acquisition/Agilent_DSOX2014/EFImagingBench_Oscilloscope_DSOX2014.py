import pyvisa
import numpy as np
import time

class OscilloscopeDSOX2014AController:
    def __init__(self):
        self.scope = None
        self.model = None
        self.connect()

    def connect(self):
        print("[Oscilloscope Controller] Connexion automatique à l'oscilloscope...")
        rm = pyvisa.ResourceManager()
        devices = rm.list_resources()
        usb_devices = [d for d in devices if "USB" in d]
        if not usb_devices:
            raise Exception("Aucun oscilloscope USB trouvé.")
        self.scope = rm.open_resource(usb_devices[0])
        self.scope.timeout = 5000
        self.model = self.scope.query("*IDN?").strip()
        print(f"[Oscilloscope Controller] Modèle détecté : {self.model}")
        if "DSO-X 2014A" not in self.model:
            print(f"[Oscilloscope Controller] Attention : Le modèle détecté ({self.model}) n'est pas un DSO-X 2014A.")

    def configure_channel(self, channel=1, vdiv=5.0, offset=0.0, coupling="DC", sonde_ratio=1):
        vdiv_effective = vdiv * sonde_ratio
        print(f"[Oscilloscope Controller] Configuration du canal {channel} : {vdiv_effective}V/div (vdiv={vdiv} * sonde_ratio={sonde_ratio}), offset {offset}V, couplage {coupling}")
        self.scope.write(f":CHANnel{channel}:SCALe {vdiv_effective}")
        self.scope.write(f":CHANnel{channel}:OFFSet {offset}")
        self.scope.write(f":CHANnel{channel}:COUPling {coupling}")

    def configure_acquisition(self, average_count=None):
        if average_count is not None:
            print(f"[Oscilloscope Controller] Mode acquisition : Moyennage sur {average_count}")
            self.scope.write(":ACQuire:TYPE AVERage")
            self.scope.write(f":ACQuire:COUNt {average_count}")
        else:
            print("[Oscilloscope Controller] Mode acquisition : Normal")
            self.scope.write(":ACQuire:TYPE NORMal")

    def configure_trigger(self, source="CHAN1", level=0.0, slope="POS"):
        print(f"[Oscilloscope Controller] Configuration du trigger : source={source}, niveau={level}V, pente={slope}")
        self.scope.write(f":TRIGger:EDGE:SOURce {source}")
        self.scope.write(f":TRIGger:EDGE:LEVel {level}")
        self.scope.write(f":TRIGger:EDGE:SLOPe {slope}")
        
    def configure_timebase(self, tscale, position=0.0):
        """
        Configure la base de temps de l'oscilloscope.
        
        Args:
            tscale (float): Échelle de temps en secondes par division
            position (float, optional): Position horizontale en secondes. Défaut à 0.0 (centre).
        
        Returns:
            bool: True si la configuration a réussi, False sinon
        """
        try:
            print(f"[Oscilloscope Controller] Configuration de la base de temps : {tscale*1000:.3f} ms/div, position {position*1000:.3f} ms")
            self.scope.write(f":TIMebase:SCALe {tscale}")
            self.scope.write(f":TIMebase:POSition {position}")
            
            # Vérification que la configuration a bien été appliquée
            actual_tscale = float(self.scope.query(":TIMebase:SCALe?"))
            actual_position = float(self.scope.query(":TIMebase:POSition?"))
            
            if abs(actual_tscale - tscale) > tscale * 0.01 or abs(actual_position - position) > 0.01:
                print(f"[Oscilloscope Controller] Attention : Valeurs appliquées différentes de celles demandées.")
                print(f"  Demandé : {tscale*1000:.3f} ms/div, {position*1000:.3f} ms")
                print(f"  Appliqué : {actual_tscale*1000:.3f} ms/div, {actual_position*1000:.3f} ms")
                return False
            return True
        except Exception as e:
            print(f"[Oscilloscope Controller] Erreur lors de la configuration de la base de temps : {e}")
            return False

    def get_waveform(self, channel=1):
        print("[Oscilloscope Controller] Acquisition de la forme d'onde...")
        self.scope.write(f":WAVeform:SOURce CHANnel{channel}")
        self.scope.write(":WAVeform:FORMat BYTE")
        self.scope.write(":WAVeform:DATA?")
        data = self.scope.read_raw()
        data = data[2:-1]
        y = np.frombuffer(data, dtype=np.uint8)
        y_increment = float(self.scope.query(":WAVeform:YINCrement?"))
        y_origin = float(self.scope.query(":WAVeform:YORigin?"))
        y_reference = float(self.scope.query(":WAVeform:YREFerence?"))
        voltage = (y - y_reference) * y_increment + y_origin
        tscale = float(self.scope.query(":TIMebase:SCALe?"))
        tdelay = float(self.scope.query(":TIMebase:POSition?"))
        time_axis = np.linspace(tdelay - 5*tscale, tdelay + 5*tscale, len(voltage))
        return time_axis, voltage

    def get_measurements(self, channel=1):
        print(f"[Oscilloscope Controller] Lecture des mesures automatiques sur le canal {channel}...")
        measures = {}
        source = f"CHANnel{channel}"
        for m in ["FREQ", "VPP", "VMAX", "VMIN", "VAMP", "VRMS", "PERIOD", "FALL"]:
            try:
                # Spécifier la source pour chaque mesure pour éviter les ambiguïtés
                val = float(self.scope.query(f":MEASure:{m}? {source}"))
                measures[m] = val
            except:
                measures[m] = None
        return measures

    def close(self):
        if self.scope is not None:
            self.scope.close()
            print("[Oscilloscope Controller] Connexion oscilloscope fermée.")

    def optimize_vdiv(self, channel=1, margin=0.9, vdiv_min=0.01, vdiv_max=None, coupling="AC", vdiv_init=None, sonde_ratio=1):
        """
        Optimise l'échelle verticale pour viser ~90% de la dynamique écran.
        Utilise l'autoscale pour trouver rapidement les paramètres adaptés au signal.
        """
        # Utiliser l'autoscale pour trouver automatiquement les paramètres adaptés au signal
        print("[Oscilloscope Controller] Exécution de l'autoscale...")
        self.scope.write(":AUToscale")
        time.sleep(3.0)  # Attendre que l'autoscale soit terminé
        
        # Récupérer les paramètres actuels
        vdiv_auto = float(self.scope.query(f":CHANnel{channel}:SCALe?")) / sonde_ratio
        
        return vdiv_auto
        # # Le reste de la fonction reste inchangé
        # # Déterminer la dynamique max selon la sonde
        # if vdiv_max is None:
        #     vdiv_max = 5  # 5V/div sans sonde, sera multiplié par sonde_ratio dans configure_channel
        # if vdiv_init is None:
        #     vdiv = vdiv_max
        # else:
        #     vdiv = vdiv_init

        # # Sauvegarder le mode d'acquisition actuel
        # current_acq_type = self.scope.query(":ACQuire:TYPE?")
        # current_acq_count = self.scope.query(":ACQuire:COUNt?")
        
        # # Configurer en mode acquisition simple pour l'optimisation
        # self.configure_acquisition(average_count=1)
        
        # essais = []
        # vdiv_found = False
        # Vpp = None

        # for _ in range(10):  # Limite à 10 essais pour éviter les boucles infinies
        #     self.configure_channel(channel=channel, vdiv=vdiv, offset=0.0, coupling=coupling, sonde_ratio=sonde_ratio)
        #     time.sleep(0.02)
        #     measures = self.get_measurements(channel)
        #     Vpp = measures.get('VPP', None)
        #     try:
        #         vpp_val = float(Vpp)
        #         if np.isnan(vpp_val) or vpp_val < 1e-3 or vpp_val > 1e3:
        #             essais.append((vdiv, Vpp))
        #             vdiv = max(vdiv / 2, vdiv_min)
        #             continue
        #         # Si le signal occupe moins d'une division, on réduit encore
        #         if vpp_val < vdiv * sonde_ratio:  # Comparer avec vdiv effectif
        #             essais.append((vdiv, Vpp))
        #             vdiv = max(vdiv / 2, vdiv_min)
        #             continue
        #         # Sinon, on a trouvé un vdiv raisonnable
        #         essais.append((vdiv, Vpp))
        #         vdiv_found = True
        #         break
        #     except Exception:
        #         essais.append((vdiv, Vpp))
        #         vdiv = max(vdiv / 2, vdiv_min)
        #         continue

        # if not vdiv_found:
        #     # Restaurer le mode d'acquisition initial
        #     self.scope.write(f":ACQuire:TYPE {current_acq_type}")
        #     self.scope.write(f":ACQuire:COUNt {current_acq_count}")
        #     return False, None, None, essais

        # # Ajuste pour viser 90% de la dynamique
        # target_ratio = 8 * margin  # 8 divisions * 0.9
        # vdiv_target = float(Vpp) / target_ratio / sonde_ratio  # Diviser par sonde_ratio car configure_channel va multiplier
        # vdiv_target = min(max(vdiv_target, vdiv_min), vdiv_max)
        # self.configure_channel(channel=channel, vdiv=vdiv_target, offset=0.0, coupling=coupling, sonde_ratio=sonde_ratio)
        # time.sleep(0.02)
        # measures = self.get_measurements(channel)
        # Vpp_final = measures.get('VPP', None)
        # essais.append((vdiv_target, Vpp_final))

        # # Restaurer le mode d'acquisition initial
        # self.scope.write(f":ACQuire:TYPE {current_acq_type}")
        # self.scope.write(f":ACQuire:COUNt {current_acq_count}")

        # return True, vdiv_target, Vpp_final, essais

    def measure_phase(self, ch1, ch2):
        """
        Mesure le déphasage (en degrés) entre deux canaux via la commande SCPI.
        Lève une exception si la commande n'est pas supportée.
        """
        try:
            phase_deg = float(self.scope.query(f":MEASure:PHASe? CHANnel{ch1},CHANnel{ch2}"))
            return phase_deg
        except Exception as e:
            raise RuntimeError(f"Commande SCPI de mesure de phase non supportée ou erreur : {e}")

# Exemple d'utilisation (peut être supprimé pour usage en import)
if __name__ == "__main__":
    try:
        o = OscilloscopeDSOX2014AController()
        o.configure_channel(channel=1, vdiv=35.0)
        o.configure_acquisition(average_count=64)
        o.configure_trigger(source="CHAN1", level=0.0, slope="POS")
        time.sleep(1)
        t, v = o.get_waveform(channel=1)
        measures = o.get_measurements(channel=1)
        print("\n--- Résumé des mesures ---")
        for k, val in measures.items():
            print(f"{k}: {val}")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        plt.plot(t, v)
        plt.title("Test : Forme d'onde brute (Canal 1)")
        plt.xlabel("Temps (s)")
        plt.ylabel("Tension (V)")
        plt.grid(True)
        plt.show()
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        if 'o' in locals():
            o.close() 