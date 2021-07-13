# NVDA Add-on: Speech History
# Copyright (C) 2012 Tyler Spivey
# Copyright (C) 2015-2017 James Scholes
# This add-on is free software, licensed under the terms of the GNU General Public License (version 2).
# See the file LICENSE for more details.

from collections import deque

import addonHandler
import api
import config
from eventHandler import FocusLossCancellableSpeechCommand
from globalCommands import SCRCAT_SPEECH
import globalPluginHandler
import gui
from queueHandler import eventQueue, queueFunction
from speech import speech
import speechViewer
import tones
import ui

from .interface import *

addonHandler.initTranslation()

oldSpeak = speech.speak
history_pos = 0


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		confspec = {
			'maxHistoryLength': 'integer(default=500)',
			'trimWhitespaceFromStart': 'boolean(default=false)',
			'trimWhitespaceFromEnd': 'boolean(default=false)',
		}
		config.conf.spec['speechHistory'] = confspec
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SpeechHistorySettingsPanel)

		self._history = deque(maxlen=config.conf['speechHistory']['maxHistoryLength'])
		global oldSpeak
		oldSpeak = speech.speak
		speech.speak = self.mySpeak

	def script_copyLast(self, gesture):
		text = self.getSequenceText(self._history[history_pos])
		if config.conf['speechHistory']['trimWhitespaceFromStart']:
			text = text.lstrip()
		if config.conf['speechHistory']['trimWhitespaceFromEnd']:
			text = text.rstrip()
		if api.copyToClip(text):
			tones.beep(1500, 120)

	# Translators: Documentation string for copy currently selected speech history item script
	script_copyLast.__doc__ = _('Copy the currently selected speech history item to the clipboard, which by default will be the most recently spoken text by NVDA.')
	script_copyLast.category = SCRCAT_SPEECH

	def script_prevString(self, gesture):
		global history_pos
		history_pos += 1
		if history_pos > len(self._history) - 1:
			tones.beep(200, 100)
			history_pos -= 1

		oldSpeak(self._history[history_pos])

	# Translators: Documentation string for previous speech history item script
	script_prevString.__doc__ = _('Review the previous item in NVDA\'s speech history.')
	script_prevString.category = SCRCAT_SPEECH

	def script_nextString(self, gesture):
		global history_pos
		history_pos -= 1
		if history_pos < 0:
			tones.beep(200, 100)
			history_pos += 1

		oldSpeak(self._history[history_pos])

	# Translators: Documentation string for next speech history item script
	script_nextString.__doc__ = _('Review the next item in NVDA\'s speech history.')
	script_nextString.category = SCRCAT_SPEECH

	def terminate(self, *args, **kwargs):
		super().terminate(*args, **kwargs)
		speech.speak = oldSpeak
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SpeechHistorySettingsPanel)

	def append_to_history(self, seq):
		global history_pos
		seq = [command for command in seq if not isinstance(command, FocusLossCancellableSpeechCommand)]
		self._history.appendleft(seq)
		history_pos = 0

	def mySpeak(self, sequence, *args, **kwargs):
		print(sequence)
		oldSpeak(sequence, *args, **kwargs)
		text = self.getSequenceText(sequence)
		if text:
			queueFunction(eventQueue, self.append_to_history, sequence)

	def getSequenceText(self, sequence):
		return speechViewer.SPEECH_ITEM_SEPARATOR.join([x for x in sequence if isinstance(x, str)])

	__gestures = {
		"kb:f12":"copyLast",
		"kb:shift+f11":"prevString",
		"kb:shift+f12":"nextString",
	}

