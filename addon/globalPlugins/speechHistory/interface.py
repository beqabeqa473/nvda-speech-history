# NVDA Add-on: Speech History
# Copyright (C) 2012 Tyler Spivey
# Copyright (C) 2015-2017 James Scholes
# This add-on is free software, licensed under the terms of the GNU General Public License (version 2).
# See the file LICENSE for more details.

import addonHandler
import config
import gui
from gui import nvdaControls
import tones
import wx
addonHandler.initTranslation()

class SpeechHistorySettingsPanel(gui.SettingsPanel):
	# Translators: the label/title for the Speech History settings panel.
	title = _('Speech History')

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: the label for the preference to choose the maximum number of stored history entries
		maxHistoryLengthLabelText = _('&Maximum number of history entries (requires NVDA restart to take effect)')
		self.maxHistoryLengthEdit = helper.addLabeledControl(maxHistoryLengthLabelText, nvdaControls.SelectOnFocusSpinCtrl, min=1, max=5000, initial=config.conf["speechHistory"]["maxHistoryLength"])

		# Translators: This is the label for a combo box in the speechHistory settings dialog.
		whitespaceStripLabel = _("&Trim  spaces from:")

		whitespaceStripChoices = (
		# Translators: This is a choice of the whitespace stip choices combo box.
		_("left"),
		# Translators: This is a choice of the whitespace stip choices combo box.
		_("right"),
		# Translators: This is a choice of the whitespace stip choices combo box.
		_("both"),
		)

		self.whitespaceStripChoice = helper.addLabeledControl(whitespaceStripLabel, wx.Choice, choices=whitespaceStripChoices)
		self.whitespaceStripChoice.SetSelection(config.conf["speechHistory"]["whitespaceStrip"])

	def onSave(self):
		config.conf["speechHistory"]["maxHistoryLength"] = self.maxHistoryLengthEdit.GetValue()
		config.conf["speechHistory"]["whitespaceStrip"] = self.whitespaceStripChoice.GetSelection()


class HistoryListDialog(wx.Dialog):

	_instance = None
	def __new__(cls, *args, **kwargs):
		if HistoryListDialog._instance is None:
			return super(HistoryListDialog, cls).__new__(cls, *args, **kwargs)
		return HistoryListDialog._instance

	def __init__(self, parent, pluginInstance):
		if HistoryListDialog._instance is not None:
			return
		HistoryListDialog._instance = self
		super(HistoryListDialog, self).__init__(parent, title=_("History list"))
		self.pluginInstance = pluginInstance
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		historyListLabel = _("&History list")
		self.historyListBox = sHelper.addLabeledControl(historyListLabel, wx.ListCtrl, style=wx.LC_REPORT)
		self.historyListBox.InsertColumn(0, "Entry")
		self.historyListBox.Selection = 0
		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.historyListBox.Bind(wx.EVT_KEY_DOWN, self.processKey)
		self.historyListBox.SetFocus()
		self.CentreOnScreen()

	def __del__(self):
		HistoryListDialog._instance = None

	def update(self):
		self.historyListBox.DeleteAllItems()
		[self.historyListBox.Append([self.pluginInstance.getSequenceText(entry)]) for entry in reversed(self.pluginInstance._history)]

	def processKey(self, event):
		keyCode = event.GetKeyCode()
		if keyCode == wx.WXK_ESCAPE:
			self.Close()
		elif keyCode == wx.WXK_RETURN:
			text = self.historyListBox.GetItemText(self.historyListBox.GetFirstSelected())
			if self.pluginInstance.copyLastItem(text):
				tones.beep(1000, 120)
				self.Close()
		event.Skip()
