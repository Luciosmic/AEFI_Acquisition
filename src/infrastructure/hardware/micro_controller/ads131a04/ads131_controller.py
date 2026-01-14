import math
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator

class ADS131Controller:
    """
    Controller for ADS131A04 Acquisition Device.
    """
    def __init__(self, serial_communicator=None):
        # Allow injection of existing communicator, or create new
        if serial_communicator:
            self.communicator = serial_communicator
        else:
            self.communicator = MCU_SerialCommunicator()
            
        self.memory_state = {
            "ICLK_divider_ratio": 2,
            "Oversampling_ratio": 32
        }

    def connect(self, port, baudrate=1500000):
        return self.communicator.connect(port, baudrate)

    def disconnect(self):
        self.communicator.disconnect()

    def _iclk_value_to_code(self, iclk_value):
        mapping = {0: 0, 2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6, 14: 7}
        return mapping.get(iclk_value, 0)

    def _oversampling_value_to_code(self, oversampling_value):
        mapping = {
            4096: 0, 2048: 1, 1024: 2, 800: 3, 768: 4, 512: 5, 
            400: 6, 384: 7, 256: 8, 200: 9, 192: 10, 128: 11, 
            96: 12, 64: 13, 48: 14, 32: 15
        }
        return mapping.get(oversampling_value, 0)

    def set_iclk_divider_and_oversampling(self, iclk_value, oversampling_value):
        """Configure conjointement ICLK divider ratio et Oversampling ratio."""
        if iclk_value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            return False, "Valeur ICLK invalide"
            
        valid_oversampling_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if oversampling_value not in valid_oversampling_values:
            return False, "Valeur Oversampling invalide"
        
        iclk_code = self._iclk_value_to_code(iclk_value)
        oversampling_code = self._oversampling_value_to_code(oversampling_value)
        
        combined_value = (iclk_code * 32) + oversampling_code
        
        success, response = self.communicator.send_command(f"a14")
        if not success: return False, response
        success, response = self.communicator.send_command(f"d{combined_value}")
        if not success: return False, response
        
        self.memory_state["ICLK_divider_ratio"] = iclk_value
        self.memory_state["Oversampling_ratio"] = oversampling_value
        
        return True, f"ICLK divider ({iclk_value}) et Oversampling ratio ({oversampling_value}) configurés"

    def set_iclk_divider(self, value):
        """Configure uniquement ICLK divider ratio en préservant l'Oversampling ratio existant"""
        current_oversampling = self.memory_state["Oversampling_ratio"]
        return self.set_iclk_divider_and_oversampling(value, current_oversampling)

    def set_oversampling_ratio(self, value):
        """Configure uniquement Oversampling ratio en préservant l'ICLK divider ratio existant"""
        current_iclk = self.memory_state["ICLK_divider_ratio"]
        return self.set_iclk_divider_and_oversampling(current_iclk, value)

    def set_reference_config(self, negative_ref=False, high_res=True, ref_voltage=1, ref_selection=1):
        """Configure les références ADC (adresse 11)"""
        val_combinee = 0
        if negative_ref: val_combinee += 128
        if high_res: val_combinee += 64
        if ref_voltage == 1: val_combinee += 16
        if ref_selection == 1: val_combinee += 8
        
        success, response = self.communicator.send_command(f"a11")
        if not success: return False, response
        success, response = self.communicator.send_command(f"d{val_combinee}")
        if not success: return False, response
        
        return True, f"Références configurées (valeur: {val_combinee})"

    def set_channel_gain(self, channel_index: int, gain: int) -> tuple[bool, str]:
        """
        Set the Digital Gain for a specific channel register (ADCx).
        Based on Datasheet Section 9.6.2 (Addresses 11h to 14h).
        
        Args:
            channel_index: 1-4 (Corresponds to ADCx register)
            gain: Gain value (1, 2, 4, 8, 16)
            
        Returns:
            (success, message)
        """
        if channel_index not in [1, 2, 3, 4]:
            return False, f"Invalid channel index: {channel_index}"
            
        # Per datasheet 9.6.2: Gains 1, 2, 4, 8, 16 supported.
        available_gains = [1, 2, 4, 8, 16]
        if gain not in available_gains:
            return False, f"Invalid gain: {gain}. Supported: {available_gains}"
            
        # Map gain to bits [2:0]
        # 1->000, 2->001, 4->010, 8->011, 16->100
        gain_code = int(math.log2(gain))
        
        # Addresses:
        # ADC1: 11h (17d)
        # ADC2: 12h (18d)
        # ADC3: 13h (19d)
        # ADC4: 14h (20d)
        address = 16 + channel_index
        
        # 1. Set Address
        success_a, resp_a = self.communicator.send_command(f"a{address}")
        if not success_a:
            return False, f"Failed to set address {address}: {resp_a}"
            
        # 2. Set Data
        success_d, resp_d = self.communicator.send_command(f"d{gain_code}")
        if not success_d:
            return False, f"Failed to write gain {gain} to address {address}: {resp_d}"
            
        return True, f"Set Digital Gain {gain} (Code {gain_code}) for Register ADC{channel_index} (Addr {address})"

    def acquisition(self, n_avg=127):
        """
        Acquisition avec moyennage configurable.
        Returns:
            success (bool)
            data (list of float): List of acquired values
        """
        command = f'm{n_avg}' # send_command adds *
        success, response_str = self.communicator.send_command(command)
        if not success:
            return False, response_str
        
        # Parse response: tab separated values
        try:
            values = [float(x) for x in response_str.split('\t') if x.strip()]
            return True, values
        except ValueError:
            return False, f"Error parsing data: {response_str}"
