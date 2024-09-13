$(function () {
    function PortRetryViewModel(parameters) {
        var self = this;

        self.connection = parameters[0];
        self.settingsViewModel = parameters[1];

        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if (plugin == "PortRetry") {
                self.connection.requestData();
            }
        }

        self.onBeforeBinding = function() {
            self.settings = self.settingsViewModel.settings;
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PortRetryViewModel,
        dependencies: ["connectionViewModel", "settingsViewModel"],
        elements: ["#settings_plugin_portretry"]
    });
});
