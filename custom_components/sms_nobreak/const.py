"""Constants for the SMS Nobreak (serial UPS) integration."""

DOMAIN = "sms_nobreak"

CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"
CONF_CAPACITY_VA = "capacity_va"
CONF_POWER_FACTOR = "power_factor"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_BAUDRATE = 2400
DEFAULT_CAPACITY_VA = 700
DEFAULT_POWER_FACTOR = 0.7
DEFAULT_SCAN_INTERVAL = 5  # seconds

MANUAL_ENTRY_VALUE = "__manual__"

# --- Megatec/Voltronic-style binary protocol ---
# Frame: <cmd_byte><4 param bytes><checksum><0x0D>
# Checksum: two's complement (256 - sum) of every preceding byte.
# This framing is shared by several UPS brands using this protocol
# family, so the same constants/logic should work for other models
# that expose the same command set (only CAPACITY_VA/POWER_FACTOR
# and the serial parameters normally need to change).
CMD_STATUS = 0x51  # 'Q' - query status
CMD_UPS_NAME = 0x49  # 'I' - query UPS identification (not wired to an entity)
CMD_TEST = 0x54  # 'T' - start battery test (duration in param bytes)
CMD_STOP_TEST = 0x44  # 'D' - cancel test
CMD_TEST_UNTIL_LOW = 0x4C  # 'L' - run on battery until low

TEST_10S_PARAMS = bytes.fromhex("00100000")
TEST_5M_PARAMS = bytes.fromhex("012c0000")

STATUS_FRAME_LENGTH = 18
