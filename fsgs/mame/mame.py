import os
from fsbc.system import windows
from fsbc.task import current_task
from fsgs.input.mapper import InputMapper
from fsgs.runner import GameRunner


# noinspection PyAttributeOutsideInit
class MAMERunner(GameRunner):

    def __init__(self, fsgs):
        super().__init__(fsgs)
        # noinspection SpellCheckingInspection
        self.emulator = "multiemu-fs"
        self.mame_init()

    def mame_emulator_name(self):
        return "mame"

    def mame_init_input(self):
        """Override in inherited classes"""
        pass

    def mame_romset(self):
        """Override in inherited classes"""
        raise NotImplementedError()

    def init_input(self):
        self.mame_init_input()
        if windows:
            self.input_device_order = "DINPUT8"

    def prepare(self):
        self.configure()
        self.mame_prepare()

    def mame_init(self):
        # override in subclasses
        pass

    def mame_prepare(self):
        pass

    def configure(self):

        self.configure_romset()

        self.default_xml = ["""\ufeff<?xml version="1.0"?>
<!-- This file is autogenerated; comments and unknown tags will be stripped -->
<mameconfig version="10">
    <system name="default">\n"""]

        self.game_xml = ["""\ufeff<?xml version="1.0"?>
<!-- This file is autogenerated; comments and unknown tags will be stripped -->
<mameconfig version="10">
    <system name="{0}">\n""".format(self.romset)]

        self.add_arg("-skip_gameinfo")
        # state_dir = self.get_state_dir()
        state_dir = self.emulator_state_dir(self.mame_emulator_name())
        state_dir = state_dir + os.sep

        self.cwd_dir = self.create_temp_dir("mame-cwd")
        self.cfg_dir = self.create_temp_dir("mame-cfg")
        self.roms_dir = self.create_temp_dir("mame-roms")
        rom_path = self.roms_dir.path
        assert self.romset
        system_rom_path = os.path.join(rom_path, self.romset)
        os.makedirs(system_rom_path)

        for sha1, name in self.romset_files:
            file_uri = self.fsgs.file.find_by_sha1(sha1)
            current_task.set_progress("Preparing ROM {name}".format(name=name))
            input_stream = self.fsgs.file.open(file_uri)
            if input_stream is None:
                raise Exception("Cannot not find required ROM " + repr(name))
            path = os.path.join(system_rom_path, name)
            with open(path, "wb") as f:
                f.write(input_stream.read())

        # shutil.copy(self.get_game_file(),
        #             os.path.join(rom_path, self.romset + '.zip'))

        # MAME uses ; as path separator on all systems, apparently
        try:
            # self.args.extend(["-rompath", self.bios_dir()])
            rom_path = rom_path + ";" + self.mame_get_bios_dir()
        except:
            pass
        # rom_path = rom_path + ";" + os.path.dirname(self.get_game_file())

        # rom_path = rom_path + os.pathsep + os.path.dirname(
        #        self.get_game_file())
        self.add_arg("-rompath", rom_path)

        # copy initial nvram disk, if any, to nvram dir
        # p, e = os.path.splitext(self.get_game_file())
        # initram = p + ".nv"
        # if os.path.exists(initram):
        #    shutil.copy(initram, os.path.join(state_dir, self.romset + '.nv'))

        game_cfg_file = os.path.join(
            self.cfg_dir.path, "{romset}.cfg".format(romset=self.romset))
        self.add_arg("-cfg_directory", self.cfg_dir.path)
        self.add_arg("-nvram_directory", state_dir)
        # self.add_arg("-memcard_directory", state_dir)
        # self.add_arg("-hiscore_directory", state_dir)
        self.add_arg("-state_directory", state_dir)
        self.add_arg("-diff_directory", state_dir)

        self.add_arg("-snapshot_directory", self.screenshots_dir())
        self.add_arg("-snapname", "{0}-%i".format(self.screenshots_name()))

        # self.change_handler = GameChangeHandler(self.cfg_dir.path)
        # self.change_handler.init(
        #     os.path.join(self.get_state_dir(), "cfg"))

        self.configure_input()
        self.configure_video()

        self.game_xml.append('    </system>\n')
        self.game_xml.append('</mameconfig>\n')
        with open(game_cfg_file, 'wb') as f:
            f.write("".join(self.game_xml).encode("UTF-8"))
            print("")
            print("")
            print("".join(self.game_xml))
            print("")
            print("")

        self.default_xml.append('    </system>\n')
        self.default_xml.append('</mameconfig>\n')
        with open(os.path.join(self.cfg_dir.path, "default.cfg"), "wb") as f:
            f.write("".join(self.default_xml).encode("UTF-8"))
            print("")
            print("")
            print("".join(self.default_xml))
            print("")
            print("")

        if self.use_doubling():
            self.add_arg("-prescale", "2")

        if self.use_smoothing():
            self.add_arg("-filter")
        else:
            self.add_arg("-nofilter")

        # start mame/mess with UI keyboard keys enabled by default,
        # full keyboard can be activated with INS / Scroll-Lock
        # self.add_arg("-ui_active")

        self.mame_configure()
        self.args.append(self.romset)

    def mame_configure(self):
        # override in subclasses
        pass

    def configure_romset(self):
        self.romset, self.romset_files = self.mame_romset()
        try:
            # convert from dict to list
            # noinspection PyUnresolvedReferences
            self.romset_files = list(self.romset_files.items())
        except AttributeError:
            # already a list
            pass

    def configure_input(self):
        # return
        # FIXME: ignoring input
        self.default_xml.append("        <input>\n")
        self.game_xml.append("        <input>\n")
        ports = {}
        # for i, input in enumerate(self.inputs):
        for i, port in enumerate(self.ports):
            input_mapping = self.mame_input_mapping(i)

            mapper = MAMEInputMapper(port, input_mapping)
            for key, value in mapper.items():
                print("---->", key, value)
                if isinstance(key, tuple):
                    key, type = key
                else:
                    type = 'standard'
                if 'type=' not in key:
                    key = 'type="{0}"'.format(key)
                key = key.replace("#", str(i + 1))
                # if '/' in key:
                #     key, tag = key.split('/')
                # else:
                #     tag = None
                # if ':' in key:
                #     key, type = key.split(':')
                # else:
                #     type = 'standard'
                if 'AD_STICK' in key: # and type == 'standard':
                    analog_axis = True
                else:
                    analog_axis = False
                if analog_axis and 'AXIS' in value:
                    value = value[:value.index('AXIS') + 4]
                    # remove increment / decrement type, set type
                    # to standard since this is an analog axis
                    type = 'standard'
                ports.setdefault(key, {}).setdefault(type, set()).add(value)
        for key, port in ports.items():
            # key, tag = key
            if 'tag=' in key:
                xml = self.game_xml
                # xml.append(
                #         '            <port tag="{tag}" '
                #         'type="{key}" mask="1" default="0">'
                #         '\n'.format(tag=tag, key=key))
                # xml.append(
                #         '            <port {key}>\n'.format(key=key))
            else:
                xml = self.default_xml
                # xml.append(
                #         '            <port type="{key}">\n'.format(key=key))
                # xml.append(
                #         '            <port {key}>\n'.format(key=key))
            xml.append('            <port {key}>\n'.format(key=key))
            for type, values in port.items():
                xml.append('                <newseq type="{type}">\n'.format(
                    type=type))
                xml.append('                    ')
                for i, value in enumerate(values):
                    if i > 0:
                        xml.append(' OR ')
                    xml.append(value)
                xml.append('\n                </newseq>\n')
            xml.append('            </port>\n')
        self.default_xml.append("        </input>\n")
        self.game_xml.append("        </input>\n")

    def configure_video(self):
        if windows and False:
            self.add_arg("-video", "d3d")
        else:
            self.add_arg("-video", "opengl")

        if self.use_fullscreen():
            self.add_arg("-nowindow")
        else:
            self.add_arg("-window")

        if self.use_stretching():
            self.add_arg("-nokeepaspect")
        else:
            self.add_arg("-keepaspect")

        self.game_xml.append('        <video>\n')
        self.game_xml.append('            <screen index="0" ')
        ox, oy, sx, sy = self.mame_offset_and_scale()
        self.game_xml.append('hstretch="{0:0.6f}" '.format(sx))
        self.game_xml.append('vstretch="{0:0.6f}" '.format(sy))
        self.game_xml.append('hoffset="{0:0.6f}" '.format(ox))
        self.game_xml.append('voffset="{0:0.6f}" '.format(oy))
        self.game_xml.append('/>\n')
        self.game_xml.append('        </video>\n')

        # effect = 'none'
        # filter_mapping = {
        #     'auto': 'aperture1x2rb',
        #     'rgb': 'aperture1x2rb',
        # }
        # for filter in self.context.config.filters:
        #     try:
        #         effect = filter_mapping[filter]
        #     except KeyError:
        #         continue
        #     break
        # self.args.extend(['-effect', effect])

        video_args = []
        if self.configure_vsync():
            video_override = "mame_video_options_vsync"
            video_args.append("-waitvsync")
            video_args.append("-syncrefresh")
            if windows and False:
                # no-throttle seems to enable turbo mode (no vsync throttling)
                # when used on Windows
                pass
            else:
                video_args.append("-nothrottle")
                pass
            # if self.get_game_refresh_rate():
            #     # should always be true since vsync was enabled...
            #     self.args.extend(
            #         ["-override_fps", str(self.get_game_refresh_rate())])
            if windows and False:
                video_args.append('-notriplebuffer')
        else:
            video_override = "mame_video_options"
            if windows and False:
                video_args.append('-triplebuffer')

        # print("mame_video_options_vsync", self.config[video_override])
        # raise Exception("gnit")

        if self.config[video_override]:
            for arg in self.config[video_override].split(" "):
                arg = arg.strip()
                if arg:
                    self.add_arg(arg)
        else:
            self.add_arg(*video_args)

    def mame_offset_and_scale(self):
        ox, oy, sx, sy = 0.0, 0.0, 1.0, 1.0
        viewport = self.config["viewport"]
        if viewport:
            src, dst = viewport.split("=")
            src = src.strip()
            dst = dst.strip()
            src_x, src_y, src_w, src_h = [int(v) for v in src.split(" ")]
            dst_x, dst_y, dst_w, dst_h = [int(v) for v in dst.split(" ")]
            sx = src_w / dst_w
            sy = src_h / dst_h
            ox = (((src_x + src_w / 2) - (dst_x + dst_w / 2)) / dst_w)
            oy = ((src_y + src_h / 2) - (dst_y + dst_h / 2)) / dst_h
        return ox, oy, sx, sy

    def mame_get_bios_dir(self):
        for dir in self.resources_dirs():
            bios_dir = os.path.join(dir, self.context.game.platform)
            if os.path.exists(bios_dir):
                return bios_dir
        raise Exception("Could not find bios dir")

    def finish(self):
        # if os.path.exists(os.path.join(self.cfg_dir.path, "default.cfg")):
        #     os.unlink(os.path.join(self.cfg_dir.path, "default.cfg"))
        # self.change_handler.update(
        #     os.path.join(self.get_state_dir(), "cfg"))
        pass


class MAMEInputMapper(InputMapper):

    def axis(self, axis, positive):
        axis_str = ["X", "Y", "Z", "RX", "RY", "RZ"][axis]
        if axis == 0:
            dir_str = "RIGHT" if positive else "LEFT"
        elif axis == 1:
            dir_str = "DOWN" if positive else "UP"
        else:
            # FIXME: Check this
            dir_str = "POS" if positive else "NEG"
        return "JOYCODE_%d_%sAXIS_%s_SWITCH" % (
            self.device.index + 1, axis_str, dir_str)

    def hat(self, hat, direction):
        if windows and False:
            dir_str = {
                'left': 'L',
                'right': 'R',
                'up': 'U',
                'down': 'D',
            }[direction]
            return "JOYCODE_{0}_HATSWITCH{1}".format(
                self.device.index + 1, dir_str)
        else:
            dir_str = {
                'left': 'LEFT',
                'right': 'RIGHT',
                'up': 'UP',
                'down': 'DOWN',
            }[direction]
            # in older MAME/MESS versions, hat 0 was specified here as 0,
            # but in recent versions, the first hat is called 1 in the config
            return "JOYCODE_{0}_HAT{1}{2}".format(
                self.device.index + 1, hat + 1, dir_str)

    def button(self, button):
        return "JOYCODE_{0}_BUTTON{1}".format(
            self.device.index + 1, button + 1)

    def key(self, key):
        return "KEYCODE_" + mame_key_codes[key.sdl_name[5:].upper()]


mame_key_codes = {
    "BACKSPACE": "BACKSPACE",
    # "TAB": 9,
    # "CLEAR": 12,
    "RETURN": "ENTER",
    # "PAUSE": 19,
    # "ESCAPE": 27,
    "SPACE": "SPACE",
    # "EXCLAIM": 33,
    # "QUOTEDBL": 34,
    # "HASH": 35,
    # "DOLLAR": 36,
    # "AMPERSAND": 38,
    # "QUOTE": 39,
    # "LEFTPAREN": 40,
    # "RIGHTPAREN": 41,
    # "ASTERISK": 42,
    # "PLUS": 43,
    "COMMA": "COMMA",
    # "MINUS": 45,
    # "PERIOD": 46,
    # "SLASH": 47,
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    # "COLON": 58,
    # "SEMICOLON": 59,
    # "LESS": 60,
    # "EQUALS": 61,
    # "GREATER": 62,
    # "QUESTION": 63,
    # "AT": 64,
    "LEFTBRACKET": "[",
    # "BACKSLASH": 92,
    "RIGHTBRACKET": "]",
    # "CARET": 94,
    # "UNDERSCORE": 95,
    # "BACKQUOTE": 96,
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "E",
    "F": "F",
    "G": "G",
    "H": "H",
    "I": "I",
    "J": "J",
    "K": "K",
    "L": "L",
    "M": "M",
    "N": "N",
    "O": "O",
    "P": "P",
    "Q": "Q",
    "R": "R",
    "S": "S",
    "T": "T",
    "U": "U",
    "V": "V",
    "W": "W",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
    "DELETE": "DEL",
    # "WORLD_0": 160,
    # "WORLD_1": 161,
    # "WORLD_2": 162,
    # "WORLD_3": 163,
    # "WORLD_4": 164,
    # "WORLD_5": 165,
    # "WORLD_6": 166,
    # "WORLD_7": 167,
    # "WORLD_8": 168,
    # "WORLD_9": 169,
    # "WORLD_10": 170,
    # "WORLD_11": 171,
    # "WORLD_12": 172,
    # "WORLD_13": 173,
    # "WORLD_14": 174,
    # "WORLD_15": 175,
    # "WORLD_16": 176,
    # "WORLD_17": 177,
    # "WORLD_18": 178,
    # "WORLD_19": 179,
    # "WORLD_20": 180,
    # "WORLD_21": 181,
    # "WORLD_22": 182,
    # "WORLD_23": 183,
    # "WORLD_24": 184,
    # "WORLD_25": 185,
    # "WORLD_26": 186,
    # "WORLD_27": 187,
    # "WORLD_28": 188,
    # "WORLD_29": 189,
    # "WORLD_30": 190,
    # "WORLD_31": 191,
    # "WORLD_32": 192,
    # "WORLD_33": 193,
    # "WORLD_34": 194,
    # "WORLD_35": 195,
    # "WORLD_36": 196,
    # "WORLD_37": 197,
    # "WORLD_38": 198,
    # "WORLD_39": 199,
    # "WORLD_40": 200,
    # "WORLD_41": 201,
    # "WORLD_42": 202,
    # "WORLD_43": 203,
    # "WORLD_44": 204,
    # "WORLD_45": 205,
    # "WORLD_46": 206,
    # "WORLD_47": 207,
    # "WORLD_48": 208,
    # "WORLD_49": 209,
    # "WORLD_50": 210,
    # "WORLD_51": 211,
    # "WORLD_52": 212,
    # "WORLD_53": 213,
    # "WORLD_54": 214,
    # "WORLD_55": 215,
    # "WORLD_56": 216,
    # "WORLD_57": 217,
    # "WORLD_58": 218,
    # "WORLD_59": 219,
    # "WORLD_60": 220,
    # "WORLD_61": 221,
    # "WORLD_62": 222,
    # "WORLD_63": 223,
    # "WORLD_64": 224,
    # "WORLD_65": 225,
    # "WORLD_66": 226,
    # "WORLD_67": 227,
    # "WORLD_68": 228,
    # "WORLD_69": 229,
    # "WORLD_70": 230,
    # "WORLD_71": 231,
    # "WORLD_72": 232,
    # "WORLD_73": 233,
    # "WORLD_74": 234,
    # "WORLD_75": 235,
    # "WORLD_76": 236,
    # "WORLD_77": 237,
    # "WORLD_78": 238,
    # "WORLD_79": 239,
    # "WORLD_80": 240,
    # "WORLD_81": 241,
    # "WORLD_82": 242,
    # "WORLD_83": 243,
    # "WORLD_84": 244,
    # "WORLD_85": 245,
    # "WORLD_86": 246,
    # "WORLD_87": 247,
    # "WORLD_88": 248,
    # "WORLD_89": 249,
    # "WORLD_90": 250,
    # "WORLD_91": 251,
    # "WORLD_92": 252,
    # "WORLD_93": 253,
    # "WORLD_94": 254,
    # "WORLD_95": 255,
    "KP0": "0PAD",
    "KP1": "1PAD",
    "KP2": "2PAD",
    "KP3": "3PAD",
    "KP4": "4PAD",
    "KP5": "5PAD",
    "KP6": "6PAD",
    "KP7": "7PAD",
    "KP8": "8PAD",
    "KP9": "9PAD",
    "KP_PERIOD": "DELPAD",
    "KP_DIVIDE": "SLASHPAD",
    "KP_MULTIPLY": "ASTERISK",
    "KP_MINUS": "MINUSPAD",
    "KP_PLUS": "PLUSPAD",
    "KP_ENTER": "ENTERPAD",
    # "KP_EQUALS": 272,
    "UP": "UP",
    "DOWN": "DOWN",
    "RIGHT": "RIGHT",
    "LEFT": "LEFT",
    "INSERT": "INSERT",
    "HOME": "HOME",
    "END": "END",
    "PAGEUP": "PGDN",
    "PAGEDOWN": "PGUP",
    "F1": "F1",
    "F2": "F2",
    "F3": "F3",
    "F4": "F4",
    "F5": "F5",
    "F6": "F6",
    "F7": "F7",
    "F8": "F8",
    "F9": "F9",
    "F10": "F10",
    "F11": "F11",
    "F12": "F12",
    # "F13": 294,
    # "F14": 295,
    # "F15": 296,
    # "NUMLOCK": 300,
    # "CAPSLOCK": 301,
    # "SCROLLOCK": 302,
    "RSHIFT": "RSHIFT",
    "LSHIFT": "LSHIFT",
    "RCTRL": "RCONTROL",
    "LCTRL": "LCONTROL",
    "RALT": "RALT",
    "LALT": "LALT",
    # "RMETA": 309,
    # "LMETA": 310,
    # "LSUPER": 311,
    # "RSUPER": 312,
    # "MODE": 313,
    # "COMPOSE": 314,
    # "HELP": 315,
    # "PRINT": 316,
    # "SYSREQ": 317,
    # "BREAK": 318,
    # "MENU": 319,
    # "POWER": 320,
    # "EURO": 321,
    # "UNDO": 322,
}
