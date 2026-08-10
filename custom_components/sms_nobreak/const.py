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
# Duration encoding for CMD_TEST is the target minutes * 100 (hundredths of a
# minute), packed big-endian in the first two param bytes - confirmed against
# real device timing: raw word 300 (0x012C) reliably ran for exactly 180s
# (3.00 min), and 16 (0x0010, the 10s-test constant) is consistent with
# 0.16 min (~9.6s). The value below was originally 0x012C (300 = "300
# seconds", an incorrect assumption), which produced a 3-minute test instead
# of 5. 500 (0x01F4) = 5.00 min * 100 gives a true 5-minute test.
TEST_5M_PARAMS = bytes.fromhex("01f40000")

STATUS_FRAME_LENGTH = 18
