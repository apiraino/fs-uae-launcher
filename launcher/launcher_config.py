import io
import os
import hashlib
import traceback
from configparser import ConfigParser, NoSectionError

from fsbc.paths import Paths

from fsgs.context import fsgs
from fsgs.ChecksumTool import ChecksumTool
from fsgs.amiga.Amiga import Amiga
from fsgs.amiga.ValueConfigLoader import ValueConfigLoader
from fsgs.FSGSDirectories import FSGSDirectories
from .launcher_settings import LauncherSettings
from fsbc.signal import Signal


# the order of the following keys is significant (for some keys).
# multiple options should be set in this order since some options will
# implicitly change other options. examples:
# - amiga model can change kickstart and joystick modes
# - file options should be set before corresponding sha1 options
from fsgs.platform import PlatformHandler

cfg = [
    ("amiga_model",           "",     "checksum", "sync"),
    ("ntsc_mode",             "",         "checksum", "sync"),
    ("accuracy",              "",         "checksum", "sync"),
    ("chip_memory",           "",         "checksum", "sync"),
    ("slow_memory",           "",         "checksum", "sync"),
    ("fast_memory",           "",         "checksum", "sync"),
    ("zorro_iii_memory",      "",         "checksum", "sync"),
    ("bsdsocket_library",     "",         "checksum", "sync"),
    ("uaegfx_card",           "",         "checksum", "sync"),
    ("joystick_port_0",       ""),
    ("joystick_port_0_mode",  "",         "checksum", "sync"),
    ("joystick_port_0_autofire",  "",     "checksum", "sync"),
    ("joystick_port_1",       ""),
    ("joystick_port_1_mode",  "",         "checksum", "sync"),
    ("joystick_port_1_autofire",  "",     "checksum", "sync"),
    ("joystick_port_2",       ""),
    ("joystick_port_2_mode",  "",         "checksum", "sync"),
    ("joystick_port_2_autofire",  "",     "checksum", "sync"),
    ("joystick_port_3",       ""),
    ("joystick_port_3_mode",  "",         "checksum", "sync"),
    ("joystick_port_3_autofire",  "",     "checksum", "sync"),

    ("floppy_drive_count",    "",         "checksum", "sync"),
    ("cdrom_drive_count",     "",         "checksum", "sync"),

    # this is not an Amiga device, so no need to checksum / sync
    ("joystick_port_4_mode",  "",         "custom"),

    ("kickstart_file",        ""),
    ("x_kickstart_file",      "",                             "nosave"),
    ("x_kickstart_file_sha1", "",         "checksum", "sync", "nosave"),
    ("kickstart_ext_file",    ""),
    ("x_kickstart_ext_file",  "",                             "nosave"),
    ("x_kickstart_ext_file_sha1", "",     "checksum", "sync", "nosave"),

    ("x_whdload_args",        "",         "checksum", "sync"),
    ("x_whdload_version",     "",     "checksum", "sync"),
    ("floppy_drive_count",    "",         "checksum", "sync", "custom"),
    ("floppy_drive_speed",    "",         "checksum", "sync", "custom"),
    ("cdrom_drive_count",     "",         "checksum", "sync", "custom"),
    ("dongle_type",           "",         "checksum", "sync", "custom"),

    ("__netplay_game",        "",         "checksum", "sync"),
    ("__netplay_password",    "",         "checksum", "sync"),
    ("__netplay_players",     "",         "checksum", "sync"),
    ("__netplay_port",        "",                     "sync"),
    ("__netplay_addresses",   "",         "checksum", "sync"),
    ("__netplay_host",        ""),
    ("__netplay_ready",       ""),
    ("__netplay_state_dir_name",  "",     "checksum", "sync"),
    ("__version",             "FIXME"),
    ("__error",               ""),
    ("x_game_uuid",           ""),
    ("x_game_xml_path",       ""),
    ("title",                 "",                             "custom"),
    ("sub_title",             "",                             "custom"),
    ("viewport",              "",                             "custom"),

    ("year",                  ""),
    ("developer",             ""),
    ("publisher",             ""),
    ("languages",             ""),
    ("players",               ""),
    ("protection",            ""),
    ("hol_url",               ""),
    ("wikipedia_url",         ""),
    ("database_url",          ""),
    ("lemon_url",             ""),
    ("mobygames_url",         ""),
    ("amigamemo_url",         ""),
    ("whdload_url",           ""),
    ("mobygames_url",         ""),
    ("longplay_url",          ""),
    ("__variant_rating",      ""),
    ("variant_rating",        ""),
    ("variant_uuid",          ""),
    
    ("download_file",         ""),
    ("download_page",         ""),
    ("download_terms",        ""),
    ("download_notice",       ""),

    ("x_missing_files",       ""),
    ("x_game_notice",         ""),
    ("x_variant_notice",      ""),
    ("x_variant_warning",      ""),
    ("x_variant_error",      ""),
    ("x_joy_emu_conflict",    ""),

    ("screen1_sha1",          ""),
    ("screen2_sha1",          ""),
    ("screen3_sha1",          ""),
    ("screen4_sha1",          ""),
    ("screen5_sha1",          ""),
    ("front_sha1",            ""),
    ("title_sha1",            ""),

    ("mouse_integration", "", "checksum", "sync"),
]

for _i in range(Amiga.MAX_FLOPPY_DRIVES):
    cfg.append(("floppy_drive_{0}".format(_i), ""))
    cfg.append(("x_floppy_drive_{0}_sha1".format(_i),
                "", "checksum", "sync", "nosave"))
for _i in range(Amiga.MAX_FLOPPY_IMAGES):
    cfg.append(("floppy_image_{0}".format(_i), ""))
    cfg.append(("x_floppy_image_{0}_sha1".format(_i),
                "", "checksum", "sync", "nosave"))
for _i in range(Amiga.MAX_CDROM_DRIVES):
    cfg.append(("cdrom_drive_{0}".format(_i), ""))
    cfg.append(("x_cdrom_drive_{0}_sha1".format(_i),
                "", "checksum", "sync", "nosave"))
for _i in range(Amiga.MAX_CDROM_IMAGES):
    cfg.append(("cdrom_image_{0}".format(_i), ""))
    cfg.append(("x_cdrom_image_{0}_sha1".format(_i),
                "", "checksum", "sync", "nosave"))
for _i in range(Amiga.MAX_HARD_DRIVES):
    cfg.append(("hard_drive_{0}".format(_i), ""))
    cfg.append(("hard_drive_{0}_label".format(_i),
                "", "checksum", "sync", "custom"))
    cfg.append(("hard_drive_{0}_priority".format(_i),
                "", "checksum", "sync", "custom"))
    cfg.append(("x_hard_drive_{0}_sha1".format(_i),
                "", "checksum", "sync", "nosave"))


class LauncherConfig(object):

    config_keys = [x[0] for x in cfg]

    default_config = {}
    for c in cfg:
        default_config[c[0]] = c[1]

    key_order = [x[0] for x in cfg]
    checksum_keys = [x[0] for x in cfg if "checksum" in x]
    sync_keys_list = [x[0] for x in cfg if "sync" in x]
    sync_keys_set = set(sync_keys_list)
    no_custom_config = [x[0] for x in cfg if "custom" not in x]

    no_custom_config.append("__changed")
    no_custom_config.append("__ready")
    no_custom_config.append("__config_name")
    # no_custom_config.append("__database")
    # no_custom_config.append("x_whdload_icon")
    # no_custom_config.append("platform")

    dont_save_keys_set = set([x[0] for x in cfg if "nosave" in x])

    reset_values = {}
    for i in range(Amiga.MAX_FLOPPY_DRIVES):
        reset_values["floppy_drive_{0}".format(i)] = \
            ("x_floppy_drive_{0}_sha1".format(i), "")
    for i in range(Amiga.MAX_FLOPPY_IMAGES):
        reset_values["floppy_image_{0}".format(i)] = \
            ("x_floppy_image_{0}_sha1".format(i), "")
    for i in range(Amiga.MAX_CDROM_DRIVES):
        reset_values["cdrom_drive_{0}".format(i)] = \
            ("x_cdrom_drive_{0}_sha1".format(i), "")
    for i in range(Amiga.MAX_CDROM_IMAGES):
        reset_values["cdrom_image_{0}".format(i)] = \
            ("x_cdrom_image_{0}_sha1".format(i), "")
    for i in range(Amiga.MAX_HARD_DRIVES):
        reset_values["hard_drive_{0}".format(i)] = \
            ("x_hard_drive_{0}_sha1".format(i), "")
    reset_values["x_kickstart_file"] = ("x_kickstart_file_sha1", "")
    reset_values["x_kickstart_ext_file"] = ("x_kickstart_ext_file_sha1", "")

    # config = default_config.copy()
    # config_listeners = []

    @classmethod
    def copy(cls):
        return fsgs.config.copy()

    @classmethod
    def get(cls, key, default=""):
        return fsgs.config.get(key, default)

    @classmethod
    def add_listener(cls, listener):
        # deprecated
        Signal("fsgs:config").connect(getattr(listener, "on_config"))

    @classmethod
    def remove_listener(cls, listener):
        # deprecated
        Signal("fsgs:config").disconnect(getattr(listener, "on_config"))

    @classmethod
    def set(cls, key, value):
        fsgs.config.set(key, value)

    @classmethod
    def set_multiple(cls, items):
        fsgs.config.set(items)

    @classmethod
    def update_from_config_dict(cls, config_dict):
        changes = []
        for key, value in config_dict.items():
            if key in fsgs.config.values:
                if fsgs.config.values[key] != value:
                    changes.append((key, value))
            else:
                changes.append((key, value))
        cls.set_multiple(changes)

    @classmethod
    def sync_items(cls):
        for key, value in fsgs.config.values.items():
            if key in cls.sync_keys_set:
                yield key, value

    @classmethod
    def checksum(cls):
        return cls.checksum_config(fsgs.config.copy())

    @classmethod
    def checksum_config(cls, config):
        s = hashlib.sha1()
        for key in cls.checksum_keys:
            value = config[key]
            s.update(str(value).encode("UTF-8"))
        return s.hexdigest()

    @classmethod
    def update_kickstart_in_config_dict(cls, config_dict):
        print("update_kickstart_in_config")
        model = config_dict.setdefault(
            "amiga_model", cls.default_config["amiga_model"])

        kickstart_file = config_dict.setdefault("kickstart_file", "")
        if kickstart_file:
            config_dict["x_kickstart_file"] = config_dict["kickstart_file"]
            if kickstart_file == "internal":
                config_dict["x_kickstart_file_sha1"] = Amiga.INTERNAL_ROM_SHA1
            else:
                # FIXME: set checksum
                pass
        else:
            checksums = Amiga.get_model_config(model)["kickstarts"]
            for checksum in checksums:
                path = fsgs.file.find_by_sha1(checksum)
                if path:
                    config_dict["x_kickstart_file"] = path
                    config_dict["x_kickstart_file_sha1"] = checksum
                    break
            else:
                print("WARNING: no suitable kickstart file found")
                config_dict["x_kickstart_file"] = ""
                config_dict["x_kickstart_file_sha1"] = Amiga.INTERNAL_ROM_SHA1

        if config_dict.setdefault("kickstart_ext_file", ""):
            config_dict["x_kickstart_ext_file"] = \
                config_dict["kickstart_ext_file"]
            # FIXME: set checksum
        else:
            checksums = Amiga.get_model_config(model)["ext_roms"]
            if len(checksums) == 0:
                config_dict["x_kickstart_ext_file"] = ""
                config_dict["x_kickstart_ext_file_sha1"] = ""
            else:
                for checksum in checksums:
                    path = fsgs.file.find_by_sha1(checksum)
                    if path:
                        config_dict["x_kickstart_ext_file"] = path
                        config_dict["x_kickstart_ext_file_sha1"] = checksum
                        break
                else:
                    # print("WARNING: no suitable kickstart ext file found")
                    config_dict["x_kickstart_ext_file"] = ""
                    config_dict["x_kickstart_ext_file_sha1"] = ""
                    # Warnings.set("hardware", "kickstart_ext",
                    #              "No suitable extended kickstart found")
                    # FIXME: set sha1 and name x_options also

    @classmethod
    def update_kickstart(cls):
        cls.set_kickstart_from_model()

    @classmethod
    def set_kickstart_from_model(cls):
        print("set_kickstart_from_model")
        config_dict = fsgs.config.values.copy()
        cls.update_kickstart_in_config_dict(config_dict)
        cls.update_from_config_dict(config_dict)

    @classmethod
    def load_default_config(cls):
        print("load_default_config")
        cls.load({})
        # FIXME: remove use of config_base
        LauncherSettings.set("config_base", "")
        LauncherSettings.set("config_name", "Unnamed Configuration")
        LauncherSettings.set("config_path", "")
        LauncherSettings.set("config_xml_path", "")

    @classmethod
    def load(cls, config):
        update_config = {}
        for key, value in cls.default_config.items():
            update_config[key] = value
        for key in list(fsgs.config.values.keys()):
            if key not in cls.default_config:
                # this is not a recognized key, so we remove it
                del fsgs.config.values[key]

        for key, value in config.items():
            # if this is a settings key, change settings instead
            if key in LauncherSettings.initialize_from_config:
                LauncherSettings.set(key, value)
            else:
                update_config[key] = value

        cls.update_kickstart_in_config_dict(update_config)
        cls.fix_loaded_config(update_config)
        # print("about to set", update_config)
        cls.set_multiple(update_config.items())
        # Settings.set("config_changed", "0")
        cls.set("__changed", "0")

        # cls.update_kickstart()

    @classmethod
    def fix_joystick_ports(cls, config):
        # from .Settings import Settings

        print("---", config["joystick_port_0"])
        print("---", config["joystick_port_1"])

        from .device_manager import DeviceManager
        available = DeviceManager.get_joystick_names()
        available.extend(["none", "mouse", "keyboard"])
        available_lower = [x.lower() for x in available]

        device_ids = DeviceManager.get_joystick_ids()
        device_ids.extend(["none", "mouse", "keyboard"])

        # remove devices from available list if specified and found
        try:
            index = available_lower.index(config["joystick_port_1"].lower())
        except ValueError:
            pass
        else:
            del available[index]
            del available_lower[index]
        try:
            index = available_lower.index(config["joystick_port_0"].lower())
        except ValueError:
            pass
        else:
            del available[index]
            del available_lower[index]

        # if config in
        # print("--------------------------------------------")
        if config["joystick_port_1_mode"] in ["joystick", "cd32 gamepad"]:
            if not config["joystick_port_1"]:
                want = LauncherSettings.get("primary_joystick").lower()
                # print("want", want)
                try:
                    index = available_lower.index(want)
                except ValueError:
                    index = -1
                print("available", available_lower)
                print("want", repr(want), "index", index)
                if index == -1:
                    index = len(available) - 1
                if index >= 0:
                    config["joystick_port_1"] = device_ids[index]
                    del available[index]
                    del available_lower[index]
                    del device_ids[index]
        elif config["joystick_port_1_mode"] in ["mouse"]:
            if not config["joystick_port_1"]:
                config["joystick_port_1"] = "mouse"
        elif config["joystick_port_1_mode"] in ["nothing"]:
            if not config["joystick_port_1"]:
                config["joystick_port_1"] = "none"

        if config["joystick_port_0_mode"] in ["joystick", "cd32 gamepad"]:
            if not config["joystick_port_0"]:
                want = LauncherSettings.get("secondary_joystick").lower()
                try:
                    index = available_lower.index(want)
                except ValueError:
                    index = -1
                # print("want", want, "index", index)
                if index == -1:
                    index = len(available) - 1
                if index >= 0:
                    config["joystick_port_0"] = device_ids[index]
                    del available[index]
                    del available_lower[index]
                    del device_ids[index]
        elif config["joystick_port_0_mode"] in ["mouse"]:
            if not config["joystick_port_0"]:
                config["joystick_port_0"] = "mouse"
        elif config["joystick_port_0_mode"] in ["nothing"]:
            if not config["joystick_port_0"]:
                config["joystick_port_0"] = "none"

    @classmethod
    def fix_loaded_config(cls, config):
        # cls.fix_joystick_ports(config)

        # FIXME: parent
        checksum_tool = ChecksumTool(None)

        def fix_file_checksum(sha1_key, key, base_dir, is_rom=False):
            path = config.get(key, "")
            # hack to synchronize URLs
            # print(repr(path))
            if path.startswith("http://") or path.startswith("https://"):
                sha1 = path
                config[sha1_key] = sha1
                return
            path = Paths.expand_path(path)
            sha1 = config.get(sha1_key, "")
            if not path:
                return
            if sha1:
                # assuming sha1 is correct
                return
            if not os.path.exists(path):
                print(repr(path), "does not exist")
                path = os.path.join(base_dir, path)
                if not os.path.exists(path):
                    print(repr(path), "does not exist")
                    return
            if os.path.isdir(path):
                # could set a fake checksum here or something, to indicate
                # that it isn't supposed to be set..
                return
            print("checksumming", repr(path))
            size = os.path.getsize(path)
            if size > 64 * 1024 * 1024:
                # not checksumming large files right now
                print("not checksumming large file")
                return

            if is_rom:
                sha1 = checksum_tool.checksum_rom(path)
            else:
                sha1 = checksum_tool.checksum(path)
            config[sha1_key] = sha1

        for i in range(Amiga.MAX_FLOPPY_DRIVES):
            fix_file_checksum(
                "x_floppy_drive_{0}_sha1".format(i),
                "floppy_drive_{0}".format(i),
                FSGSDirectories.get_floppies_dir())
        for i in range(Amiga.MAX_FLOPPY_IMAGES):
            fix_file_checksum(
                "x_floppy_image_{0}_sha1".format(i),
                "floppy_image_{0}".format(i),
                FSGSDirectories.get_floppies_dir())
        for i in range(Amiga.MAX_CDROM_DRIVES):
            fix_file_checksum(
                "x_cdrom_drive_{0}_sha1".format(i),
                "cdrom_drive_{0}".format(i),
                FSGSDirectories.get_cdroms_dir())
        for i in range(Amiga.MAX_CDROM_IMAGES):
            fix_file_checksum(
                "x_cdrom_image_{0}_sha1".format(i),
                "cdrom_image_{0}".format(i),
                FSGSDirectories.get_cdroms_dir())
        for i in range(Amiga.MAX_HARD_DRIVES):
            fix_file_checksum(
                "x_hard_drive_{0}_sha1".format(i),
                "hard_drive_{0}".format(i),
                FSGSDirectories.get_hard_drives_dir())

        # FIXME: need to handle checksums for Cloanto here
        fix_file_checksum(
            "x_kickstart_file_sha1", "x_kickstart_file",
            FSGSDirectories.get_kickstarts_dir(), is_rom=True)
        fix_file_checksum(
            "x_kickstart_ext_file_sha1", "x_kickstart_ext_file",
            FSGSDirectories.get_kickstarts_dir(), is_rom=True)

    @classmethod
    def load_file(cls, path):
        try:
            cls._load_file(path, "")
        except Exception:
            # FIXME: errors should be logged / displayed
            cls.load_default_config()
            traceback.print_exc()

    @classmethod
    def load_data(cls, data):
        print("Config.load_data")
        try:
            cls._load_file("", data)
        except Exception:
            # FIXME: errors should be logged / displayed
            cls.load_default_config()
            traceback.print_exc()

    @classmethod
    def create_fs_name(cls, name):
        name = name.replace(':', ' - ')
        name = name.replace('*', '-')
        name = name.replace('?', '')
        name = name.replace('/', '-')
        name = name.replace('\\', '-')
        name = name.replace('"', "'")
        for i in range(3):
            name = name.replace('  ', ' ')
        while name.endswith('.'):
            name = name[:-1]
        name = name.strip()
        return name

    @classmethod
    def _load_file(cls, path, data):
        if data:
            print("loading config from data")
        else:
            print("loading config from " + repr(path))
            if not os.path.exists(path):
                print("config file does not exist")
        if data:
            raise Exception("_load_file (data) not implemented")
        # if data:
        #     config_xml_path = ""
        #     loader = XMLConfigLoader()
        #     loader.load_data(data)
        #     config = loader.get_config()
        # elif path.endswith(".xml"):
        #     config_xml_path = path
        #     loader = XMLConfigLoader()
        #     loader.load_file(path)
        #     config = loader.get_config()
        else:
            config_xml_path = ""
            cp = ConfigParser(interpolation=None, strict=False)
            try:
                with io.open(path, "r", encoding="UTF-8") as f:
                    cp.readfp(f)
                # cp.read([path])
            except Exception as e:
                print(repr(e))
                return
            config = {}
            try:
                keys = cp.options("config")
            except NoSectionError:
                keys = []
            for key in keys:
                config[key] = cp.get("config", key)
            try:
                keys = cp.options("fs-uae")
            except NoSectionError:
                keys = []
            for key in keys:
                config[key] = cp.get("fs-uae", key)

        LauncherSettings.set("config_path", path)

        cls.load(config)

        config_name = config.get("__config_name", "")
        if config_name:
            config_name = cls.create_fs_name(config_name)
        else:
            config_name, ext = os.path.splitext(os.path.basename(path))

        if "(" in config_name:
            config_base = config_name.split("(")[0].strip()
        else:
            config_base = config_name
        # game = name

        # if not Config.get("title"):
        #     Config.set("title", config_base)

        LauncherSettings.set("config_base", config_base)
        LauncherSettings.set("config_name", config_name)
        LauncherSettings.set("config_xml_path", config_xml_path)
        # Settings.set("config_changed", "0")
        cls.set("__changed", "0")

    @classmethod
    def load_values(cls, values, uuid=""):
        print("loading config values", values)
        platform_id = values.get("platform", "").lower()

        if platform_id in ["amiga", "cdtv", "cd32"]:
            value_config_loader = ValueConfigLoader(uuid=uuid)
            value_config_loader.load_values(values)
            config = value_config_loader.get_config()
            cls.load(config)
            config_name = config.get("__config_name", "")

        else:
            print("Warning: Non-Amiga game loaded")
            platform_handler = PlatformHandler.create(platform_id)
            loader = platform_handler.get_loader(fsgs)
            fsgs.config.load(loader.load_values(values))
            config_name = "{0} ({1})".format(
                values.get("game_name"), values.get("platform_name"))

        LauncherSettings.set("config_path", "")

        # print("config is", config)
        # config["x_config_uuid"] = uuid

        if config_name:
            config_name = cls.create_fs_name(config_name)
        # else:
        #     config_name, ext = os.path.splitext(os.path.basename(path))

        if "(" in config_name:
            config_base = config_name.split("(")[0].strip()
        else:
            config_base = config_name
        # game = name

        # if not Config.get("title"):
        #     Config.set("title", config_base)

        LauncherSettings.set("config_base", config_base)
        LauncherSettings.set("config_name", config_name)
        LauncherSettings.set("config_xml_path", "")
        # Settings.set("config_changed", "0")
        cls.set("__changed", "0")
