import fsui
from launcher.i18n import gettext
from launcher.ui.settings.settings_page import SettingsPage


class VideoSettingsPage(SettingsPage):
    def __init__(self, parent):
        super().__init__(parent)
        icon = fsui.Icon("video-settings", "pkg:workspace")
        gettext("Video Settings")
        title = gettext("Video")
        subtitle = ""
        self.add_header(icon, title, subtitle)

        self.add_option("fullscreen")
        self.add_option("monitor")

        self.add_section(gettext("Scaling"))
        self.add_option("zoom")
        self.add_option("keep_aspect")

        self.add_section(gettext("Filters"))
        self.add_option("scanlines")
        self.add_option("rtg_scanlines")
