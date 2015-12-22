import fsui
from fs_uae_launcher.I18N import gettext
from fs_uae_launcher.ui.settings.settings_page import SettingsPage


class LoggingSettingsPage(SettingsPage):

    def __init__(self, parent):
        super().__init__(parent)
        icon = fsui.Icon("settings", "pkg:fs_uae_workspace")
        title = gettext("Logging")
        subtitle = ""
        self.add_header(icon, title, subtitle)

        label = fsui.MultiLineLabel(self, gettext(
            "The following options may affect performance, "
            "so only enable them when needed for testing or "
            "debugging purposes."), 640)
        self.layout.add(label, fill=True, margin_top=20)

        self.add_option("log_autoscale")
        self.add_option("log_input")
