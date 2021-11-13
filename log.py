import sys
from enum import IntEnum


# Log messages sent from a plugin instance are transmitted via stderr and are
# encoded with a prefix consisting of special character SOH, then the log
# level (one of t, d, i, w, e, or p - corresponding to trace, debug, info,
# warning, error and progress levels respectively), then special character
# STX.
#
# The LogTrace, LogDebug, LogInfo, LogWarning, and LogError methods, and their equivalent
# formatted methods are intended for use by plugin instances to transmit log
# messages. The LogProgress method is also intended for sending progress data.
#

def __prefix(level_char):
	start_level_char = b'\x01'
	end_level_char = b'\x02'

	ret = start_level_char + level_char + end_level_char
	return ret.decode()


def do_log(level_char, s):
	if level_char == "":
		return

	print(__prefix(level_char) + s + "\n", file=sys.stderr, flush=True)

class LogLevel(IntEnum):
	TRACE = 1
	DEBUG = 2
	INFO = 3
	WARN = 4
	ERROR = 5

class Logger:

	def __init__(self, log_level=LogLevel.ERROR, plugin=True):
		self.log_level = log_level
		self.plugin = plugin

	def __log(self, level_char, s):
		if self.plugin:
			do_log(level_char, s)
		else:
			print(s)

	def LogTrace(self, s):
		if self.log_level <= LogLevel.TRACE:
			self.__log(b't', s)


	def LogDebug(self, s):
		if self.log_level <= LogLevel.DEBUG:
			self.__log(b'd', s)


	def LogInfo(self, s):
		if self.log_level <= LogLevel.INFO:
			self.__log(b'i', s)


	def LogWarning(self, s):
		if self.log_level <= LogLevel.WARN:
			self.__log(b'w', s)


	def LogError(self, s):
		if self.log_level <= LogLevel.ERROR:
			self.__log(b'e', s)


	def LogProgress(self, p):
		if self.plugin:
			progress = min(max(0, p), 1)
			self.__log(b'p', str(progress))

log = Logger()