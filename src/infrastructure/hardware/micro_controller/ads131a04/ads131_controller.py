import logging
import math
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator

logger = logging.getLogger(__name__)


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
        logger.info("Connecting to ADS131A04 on %s (baudrate=%d)", port, baudrate)
        return self.communicator.connect(port, baudrate)

    def disconnect(self):
        logger.info("Disconnecting from ADS131A04")
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
            logger.error("Invalid ICLK divider value: %s", iclk_value)
            return False, "Valeur ICLK invalide"

        valid_oversampling_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if oversampling_value not in valid_oversampling_values:
            logger.error("Invalid oversampling value: %s", oversampling_value)
            return False, "Valeur Oversampling invalide"

        iclk_code = self._iclk_value_to_code(iclk_value)
        oversampling_code = self._oversampling_value_to_code(oversampling_value)

        combined_value = (iclk_code * 32) + oversampling_code

        success, response = self.communicator.send_command(f"a14")
        if not success:
            logger.error("Failed to set ICLK/oversampling address register: %s", response)
            return False, response
        success, response = self.communicator.send_command(f"d{combined_value}")
        if not success:
            logger.error("Failed to write ICLK/oversampling data register: %s", response)
            return False, response

        self.memory_state["ICLK_divider_ratio"] = iclk_value
        self.memory_state["Oversampling_ratio"] = oversampling_value

        logger.info("ICLK divider set to %d, oversampling ratio set to %d", iclk_value, oversampling_value)
        return True, f"ICLK divider ({iclk_value}) et Oversampling ratio ({oversampling_value}) configurés"

    def set_iclk_divider(self, value):
        """Configure uniquement ICLK divider ratio en préservant l'Oversampling ratio existant"""
        current_oversampling = self.memory_state["Oversampling_ratio"]
        return self.set_iclk_divider_and_oversampling(value, current_oversampling)

    def set_oversampling_ratio(self, value):
        """Configure uniquement Oversampling ratio en préservant l'ICLK divider ratio existant"""
        current_iclk = self.memory_state["ICLK_divider_ratio"]
        return self.set_iclk_divider_and_oversampling(current_iclk, value)

    def set_clkin_divider(self, divider: int):
        """CLK1 (adresse 13) : CLK_DIV[2:0] sur les bits 3:1, code = divider/2 -> registre = divider."""
        if divider not in [2, 4, 6, 8, 10, 12, 14]:
            logger.error("Invalid CLKIN divider value: %s", divider)
            return False, "Valeur CLKIN divider invalide"
        success, response = self.communicator.send_command("a13")
        if not success:
            logger.error("Failed to set CLKIN divider address register: %s", response)
            return False, response
        success, response = self.communicator.send_command(f"d{divider}")
        if not success:
            logger.error("Failed to write CLKIN divider data register: %s", response)
            return False, response
        logger.info("CLKIN divider set to %d", divider)
        return True, f"CLKIN divider ({divider}) configuré"

    def set_reference_config(self, negative_charge_pump=False, high_resolution=True, reference_voltage=2.442, internal_reference=True):
        """A_SYS_CFG (adresse 11). Grandeurs physiques -> bits ; seul endroit qui connaît ce registre."""
        val_combinee = 0
        if negative_charge_pump: val_combinee += 128  # Bit 7: VNCPEN
        if high_resolution: val_combinee += 64  # Bit 6: HRM
        val_combinee += 32  # Bit 5: reserved, datasheet says always write 1
        if reference_voltage == 4.0: val_combinee += 16  # Bit 4: VREF_4V (0 = 2.442 V)
        if internal_reference: val_combinee += 8  # Bit 3: INT_REFEN
        
        success, response = self.communicator.send_command(f"a11")
        if not success:
            logger.error("Failed to set reference config address register: %s", response)
            return False, response
        success, response = self.communicator.send_command(f"d{val_combinee}")
        if not success:
            logger.error("Failed to write reference config data register: %s", response)
            return False, response

        logger.info(
            "Reference config set: A_SYS_CFG=%d (reference_voltage=%sV, internal_reference=%s, high_resolution=%s, negative_charge_pump=%s)",
            val_combinee, reference_voltage, internal_reference, high_resolution, negative_charge_pump,
        )
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
            logger.error("Invalid channel index: %s", channel_index)
            return False, f"Invalid channel index: {channel_index}"

        # Per datasheet 9.6.2: Gains 1, 2, 4, 8, 16 supported.
        available_gains = [1, 2, 4, 8, 16]
        if gain not in available_gains:
            logger.error("Invalid gain %s for channel %d. Supported: %s", gain, channel_index, available_gains)
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
            logger.error("Failed to set gain address %d for channel %d: %s", address, channel_index, resp_a)
            return False, f"Failed to set address {address}: {resp_a}"

        # 2. Set Data
        success_d, resp_d = self.communicator.send_command(f"d{gain_code}")
        if not success_d:
            logger.error("Failed to write gain %d to address %d: %s", gain, address, resp_d)
            return False, f"Failed to write gain {gain} to address {address}: {resp_d}"

        logger.info("Set digital gain %d for channel %d (register ADC%d)", gain, channel_index, channel_index)
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
            logger.error("Failed to parse acquisition response: %s", response_str)
            return False, f"Error parsing data: {response_str}"
