import fsui
from .RemovableMediaGroup import RemovableMediaGroup
from .Skin import Skin
from .config.InputGroup import InputGroup
from .config.modelgroup import ModelGroup


class MainPanel(fsui.Panel):
    def __init__(self, parent):
        fsui.Panel.__init__(self, parent)
        Skin.set_background_color(self)
        self.layout = fsui.VerticalLayout()

        self.model_group = ModelGroup(self)
        self.removable_media_group = RemovableMediaGroup(self, 2)
        self.input_group = InputGroup(self)

        self.layout.add(self.model_group, fill=True)
        self.layout.add_spacer(Skin.EXTRA_GROUP_MARGIN)

        self.layout.add(self.removable_media_group, fill=True)
        self.layout.add_spacer(Skin.EXTRA_GROUP_MARGIN)

        self.layout.add(self.input_group, fill=True)
