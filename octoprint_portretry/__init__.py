# coding=utf-8
from __future__ import absolute_import

import threading
import serial

import octoprint.plugin
from octoprint.util import get_exception_string

# https://stackoverflow.com/a/13151299
class _RepeatedTimer:
	def __init__(self, interval: float, function, *args, **kwargs):
		self._timer     = None
		self.interval   = interval
		self.function   = function
		self.args       = args
		self.kwargs     = kwargs
		self.is_running = False
		self.start()

	def _run(self):
		self.is_running = False
		self.start()
		self.function(*self.args, **self.kwargs)

	def start(self):
		if not self.is_running:
			self._timer = threading.Timer(self.interval, self._run)
			self._timer.start()
			self.is_running = True

	def stop(self):
		self._timer.cancel()
		self.is_running = False

class PortRetryPlugin(octoprint.plugin.StartupPlugin,
					  octoprint.plugin.AssetPlugin,
					  octoprint.plugin.TemplatePlugin,
					  octoprint.plugin.SettingsPlugin):
	def on_after_startup(self, *args, **kwargs):
		self._logger.info(f"Port Retry {repr(args)} {repr(kwargs)}")

		interval = self._settings.get_float(['interval'], min=0.1)
		self.__timer = _RepeatedTimer(interval, self.do_auto_connect)

	def on_shutdown(self, *args, **kwargs):
		self.__timer.stop()

	def do_auto_connect(self, *args, **kwargs):
		try:
			printer_profile = self._printer_profile_manager.get_default()
			profile = printer_profile['id'] if 'id' in printer_profile else '_default'
			if not self._printer.is_closed_or_error():
				#self._logger.info('Not autoconnecting; printer already connected')
				return
			port = self._settings.get(['port'])
			portopen = False
			# try the serial port
			try:
				ser0 = serial.Serial(port)
				portopen = ser0.is_open
			except: 
				self._logger.info(f"Failed to open port {port}")				
			if portopen:
				self._logger.info(f"Attempting to connect to {port} with profile {profile}")
				self._printer.connect(port=port, profile=profile)
		except:
			self._logger.error(f"Exception in do_auto_connect {get_exception_string()}")

	def get_settings_defaults(self, *args, **kwargs):
		return dict(interval=5.0, port='/dev/ttyUSB0')

	def get_assets(self, *args, **kwargs):
		return dict(js=['js/portretry.js'])

	def get_update_information(self, *args, **kwargs):
		return dict(
			portretry=dict(
				displayName='PortRetry',
				displayVersion=self._plugin_version,

				# use github release method of version check
				type='github_release',
				user='VEhystrix',
				repo='OctoPrint-PortRetry',
				current=self._plugin_version,

				# update method: pip
				pip='https://github.com/vehystrix/OctoPrint-PortRetry/archive/{target_version}.zip'
			)
		)

	def on_settings_save(self, data):
		interval = self._settings.get_float(['interval'], min=0.1)

		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		new_interval = self._settings.get_float(['interval'], min=0.1)
		if interval != new_interval:
			self._logger.info(f"Retry interval changed to {new_interval}")
			self.__timer.stop()
			self.__timer.interval = new_interval
			self.__timer.start()


__plugin_name__ = 'PortRetry'
__plugin_pythoncompat__ = '>=2.7,<4'

def __plugin_load__():
	global __plugin_implementation__
	plugin = PortRetryPlugin()
	__plugin_implementation__ = plugin


	global __plugin_hooks__
	__plugin_hooks__ = {
		'octoprint.plugin.softwareupdate.check_config': plugin.get_update_information,
	}
