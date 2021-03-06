import fsui as fsui
from fsbc.application import app
from launcher.i18n import gettext
from launcher.launcher_settings import LauncherSettings


class FullscreenModeButton(fsui.ImageButton):
    def __init__(self, parent):
        self.window_icon = fsui.Image("launcher:res/16/fullscreen_window.png")
        self.fullscreen_icon = fsui.Image(
            "launcher:res/16/fullscreen_fullscreen.png")
        self.desktop_icon = fsui.Image(
            "launcher:res/16/fullscreen_desktop.png")
        super().__init__(parent, self.desktop_icon)
        self.set_tooltip(gettext("Toggle fullscreen mode"))
        self.set_min_width(40)
        self.fullscreen_mode = "desktop"
        self.on_setting("fullscreen_mode", app.settings["fullscreen_mode"])
        LauncherSettings.add_listener(self)

    def on_destroy(self):
        LauncherSettings.remove_listener(self)

    def on_setting(self, key, value):
        if key == "fullscreen_mode":
            if value == "fullscreen":
                self.fullscreen_mode = "fullscreen"
                self.set_image(self.fullscreen_icon)
            elif value == "window":
                self.fullscreen_mode = "window"
                self.set_image(self.window_icon)
            else:
                self.fullscreen_mode = "desktop"
                self.set_image(self.desktop_icon)

    def on_activate(self):
        if self.fullscreen_mode == "fullscreen":
            app.settings["fullscreen_mode"] = "window"
        elif self.fullscreen_mode == "window":
            app.settings["fullscreen_mode"] = ""
        else:
            app.settings["fullscreen_mode"] = "fullscreen"
