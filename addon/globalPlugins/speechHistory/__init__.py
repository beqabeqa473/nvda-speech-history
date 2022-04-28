# NVDA Add-on: Speech History
# Copyright (C) 2012 Tyler Spivey
# Copyright (C) 2015-2017 James Scholes
# This add-on is free software, licensed under the terms of the GNU General Public License (version 2).
# See the file LICENSE for more details.

import collections
from collections import deque

import addonHandler
import api
import config
from eventHandler import FocusLossCancellableSpeechCommand
from globalCommands import SCRCAT_SPEECH
import globalPluginHandler
import gui
from queueHandler import eventQueue, queueFunction
from scriptHandler import getLastScriptRepeatCount, script
from speech import speech
import speechViewer
import tones

from . import interface

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		confspec = {
			"maxHistoryLength": "integer(default=500)",
			"whitespaceStrip": "integer(default=2)",
		}
		config.conf.spec["speechHistory"] = confspec
		self.dialog = None
		self.init_history()
		self.history_pos = 0
		self.localSpeak = speech.speak
		speech.speak = self.speakDecorator(speech.speak)
		interface.init_settings(self.on_save)

	def terminate(self, *args, **kwargs):
		super().terminate(*args, **kwargs)
		interface.terminate_settings()

	def init_history(self):
		self._history = deque(maxlen=config.conf["speechHistory"]["maxHistoryLength"])

	def on_save(self):
		self.init_history()

	def speakDecorator(self, func):
		def wrapper(sequence, *args, **kwargs):
			result = func(sequence, *args, **kwargs)
			text = self.getSequenceText(sequence)
			if text and not text.isspace():
				queueFunction(eventQueue, self.append_to_history, sequence)
			return result
		return wrapper

	def append_to_history(self, seq):
		seq = [command for command in seq if not isinstance(command, FocusLossCancellableSpeechCommand)]
		self._history.appendleft(seq)

	def getSequenceText(self, sequence):
		return speechViewer.SPEECH_ITEM_SEPARATOR.join([x for x in sequence if isinstance(x, str)])

	def copyLastItem(self, text, strip = False):
		if strip:
			whitespaceStrip = config.conf["speechHistory"]["whitespaceStrip"]
			if whitespaceStrip == 0:
				text = text.lstrip()
			elif whitespaceStrip == 1:
				text = text.rstrip()
			else:
				text = text.strip()
		res = api.copyToClip(text)
		if res:
			return True
		return False

	def moveToItem(self, direction):
		if direction == 1:
			self.history_pos += 1
			if self.history_pos > len(self._history) - 1:
				tones.beep(200, 100)
				self.history_pos -= 1
		else:
			self.history_pos -= 1
			if self.history_pos < 0:
				tones.beep(200, 100)
				self.history_pos += 1
		self.localSpeak(self._history[self.history_pos])

	def openHistoryListDialog(self):
		gui.mainFrame.prePopup()
		self.dialog = HistoryListDialog(gui.mainFrame, self)
		self.dialog.update()
		self.dialog.Show()
		gui.mainFrame.postPopup()

	@script(
		# Translators: message presented in input mode, when a keystroke of an addon script is pressed.
		description=_("Show messages list."),
		gesture="kb:NVDA+shift+f12"
	)
	def script_showHistoryListDialog(self, gesture):
		wx.CallAfter(self.openHistoryListDialog)

	@script(
		# Translators: message presented in input mode, when a keystroke of an addon script is pressed.
		description = _("Copy the currently selected speech history item to the clipboard, which by default will be the most recently spoken text by NVDA."),
		category = SCRCAT_SPEECH,
		gesture = "kb:f12"
	)
	def script_copyLast(self, gesture):
		text = self.getSequenceText(self._history[self.history_pos])
		repeat = getLastScriptRepeatCount()
		if repeat > 0:
			if self.copyLastItem(text, True):
				tones.beep(1500, 120)
		else:
			if self.copyLastItem(text):
				tones.beep(1000, 120)

	@script(
		# Translators: message presented in input mode, when a keystroke of an addon script is pressed.
		description = _("Review the previous item in NVDA's speech history."),
		category = SCRCAT_SPEECH,
		gesture = "kb:shift+f11"
	)
	def script_prevString(self, gesture):
			self.moveToItem(1)

	@script(
		# Translators: message presented in input mode, when a keystroke of an addon script is pressed.
		description = _("Review the next item in NVDA's speech history."),
		category = SCRCAT_SPEECH,
		gesture = "kb:shift+f12"
	)
	def script_nextString(self, gesture):
			self.moveToItem(-1)
