import serial

import octoprint.plugin
from octoprint.util import get_exception_string, RepeatedTimer

class PortRetryPlugin(octoprint.plugin.StartupPlugin,
					  octoprint.plugin.AssetPlugin,
					  octoprint.plugin.TemplatePlugin,
					  octoprint.plugin.SettingsPlugin,
					  octoprint.plugin.EventHandlerPlugin):
	def __init__(self):
		super().__init__()

	def on_after_startup(self, *args, **kwargs):
		self._logger.info(f"PortRetry starting with interval {self.__get_interval()}")
		
		if not self._printer.is_closed_or_error(): self.__start_timer()

	def __get_interval(self) -> float:
		return self._settings.get_float(['interval'], min=0.1)
	def __create_timer(self):
		self._timer = RepeatedTimer(self.__get_interval(), self.do_auto_connect)
	def __start_timer(self):
		self.__create_timer()
		self._timer.start()
	def __stop_timer(self):
		self._timer.cancel()

	def on_shutdown(self, *args, **kwargs):
		self._timer.cancel()

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
				self._logger.debug(f"Failed to open port {port}")				
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
				displayName=self._plugin_name,
				displayVersion=self._plugin_version,

				# use github release method of version check
				type='github_release',
				user='vehystrix',
				repo='OctoPrint-PortRetry',
				current=self._plugin_version,

				# update method: pip
				pip='https://github.com/vehystrix/OctoPrint-PortRetry/archive/{target}.zip'
			)
		)

	def on_settings_save(self, data):
		interval = self._settings.get_float(['interval'], min=0.1)

		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		new_interval = self._settings.get_float(['interval'], min=0.1)
		if interval != new_interval:
			self._logger.info(f"Retry interval changed to {new_interval}")
			self.__stop_timer()
			self.__start_timer()

	def on_event(self, event: str, payload: dict):
		if not hasattr(self, '_timer'): return # only occurs during server startup

		if 'Connected' == event:
			self._logger.info('Printer connected, stopping timer')
			self.__stop_timer()
		elif 'Disconnected' == event:
			self._logger.info('Printer disconnected, starting timer')
			self.__start_timer()


__plugin_name__ = 'PortRetry'
__plugin_pythoncompat__ = '>=3,<4'

def __plugin_load__():
	global __plugin_implementation__
	plugin = PortRetryPlugin()
	__plugin_implementation__ = plugin


	global __plugin_hooks__
	__plugin_hooks__ = {
		'octoprint.plugin.softwareupdate.check_config': plugin.get_update_information,
	}
