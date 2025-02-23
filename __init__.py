from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
import lingua_franca
from ovos_backend_client.api import DeviceApi
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.log import LOG
from mycroft.util import extract_number
import sys
import os
import time
import samsungctl

class SamsungTVCtl(OVOSSkill):
    def __init__(self):
        super(SamsungTVCtl, self).__init__(name="SamsungTVCtl")

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=False,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=False)

    def initialize(self):
        DEFAULT_SETTINGS = {
            "__mycroft_skill_firstrun": "false",
            "tv": "192.168.178.91",
            "port": 55000,
            "placement": "Stube",
            "method": "legacy",
            "rc_name": "Ovos",
            "description_rc": "Beschreibung",
            "translations": {
                "hoch": "UP",
                "höher": "UP",
                "rauf": "UP",
                "nach_oben": "UP",
                "tiefer": "DOWN",
                "runter": "DOWN",
                "nach_unten": "DOWN",
                "links": "LEFT",
                "rechts": "RIGHT",
                "nehmen": "ENTER",
                "verlassen": "EXIT"
            },
            "channels": {
                "das_erste": 1,
                "erstes_programm": 1,
                "zdf": 2,
                "zweites_programm": 2,
                "ndr": 101,
                "3sat": 11,
                "arte": 153,
                "one": 127,
                "zdf_neo": 202,
                "phoenix": 152,
                "phönix": 152,
                "zdf_info": 201,
                "vox": 1204,
                "sat_1": 1205,
                "pro_sieben": 1206,
                "pro_7": 1206,
                "prosieben": 1206,
                "kabel_1": 1207,
                "rtl": 315,
                "rtl_2": 1209,
                "super_rtl": 1219,
                "ntv": 1264,
                "rtl_nitro": 1265,
                "rbb": 24,
                "br": 31,
                "bayerischer_rundfunk": 31,
                "hr": 32,
                "hessischer_rundfunk": 32,
                "bw": 33,
                "baden-württemberg": 33,
                "wdr": 110,
                "westdeutscher_rundfunk": 110,
                "mdr": 115,
                "mitteldeutscher_rundfunk": 115,
                "ard_alpha": 125,
                "tagesschau_24": 126,
                "radio_bremen": 1128
            }
        }
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        self.same_device = DeviceApi()
        self.info = self.same_device.uuid
        #self.settings["tv-neu"] = {"TV1": "BLA", "TV2": "BLUB"}
        #self.settings.store()
        #LOG.info(f"Neue settings: {str(self.settings)}.")
        #mypath = self.file_system.path
        #LOG.info(f"Systempfad ist: {self.file_system.path} oder {mypath}.")

    def on_settings_changed(self):
        self.curs_move_dict = {"nach links": "LEFT", "nach rechts": "RIGHT", "nach oben": "UP", "nach unten": "DOWN", "nehmen": "ENTER", "verlassen": "EXIT"}
        self.host = self.settings.get('tv')
        self.port = self.settings.get('port')
        self.placement = self.settings.get('placement')
        self.name_rc = self.settings.get('rc_name')
        self.method = self.settings.get('method')
        self.description_rc = self.settings.get('description_rc')
        self.translations = self.settings.get('translations')
        self.channels = self.settings.get('channels')
        self.config = {"name": self.name_rc, "description": self.description_rc,\
            "id": "", "host": self.host, "port": self.port, "method": self.method,\
            "timeout": 0}

#Main functions
    def send_keycode(self, keycode):
        '''Standard function for sending keycodes'''
        keycode = "KEY_" + keycode.upper()
        try:
            LOG.info("Keycode ist: " + str(keycode))
            #with samsungctl.Remote(self.config) as remote:
            #    remote.control(keycode)
        except Exception as e:
            LOG.info(str(e))
        finally:
            pass

#Helper functions
    def send_channel_pos(self, pos):
        '''Function for sending channel number; with multi-digit numbers \
        the values are transmitted number by number. Therefore there is a \
        small pause to consider the latency time of the LAN/WLAN or web server \
        and numbers has to be formatted as strings.'''
        if len(pos) > 1:
            i = 0
            while i < len(pos):
                self.send_keycode(pos[i])
                time.sleep(.3)
                i += 1
        else:
            self.send_keycode(pos)

    def explain_cursor_moves(self, translations):
        '''Usage of cursor based selections'''
        self.speak_dialog('cursor_moves')
        self.speak(translations)
        move = ""
        return move

    def explain_cursor_moves_source(self):
        '''Usage of cursor based selections'''
        self.speak_dialog('cursor_moves_source')
        move = ""
        return move

    def cursor_recursion(self, move):
        move = self.get_response()
        move = move.replace(" ","_").lower()
        if move != None:
            move = move.lower()
            LOG.info("Bewegung: " + move)
        else:
            LOG.info("Move ist None")
        if move == None:
            keycode = "EXIT"
            self.send_keycode(keycode)
            return
        if move in self.translations.keys():
            keycode = self.translations[move]
            if keycode == "ENTER" or keycode == "EXIT":
                self.send_keycode(keycode)
                return
            else:
                self.send_keycode(keycode)
                move = ""
                time.sleep(.3)
                self.cursor_recursion(move)
        else:
            self.speak_dialog('unknown.move', {'move': move})
            keycode = "EXIT"
            self.send_keycode(keycode)

    def switch_by_channel_name(self, channel):
        channel = channel.replace(' ','_').lower()
        channel = self.check_channel(channel)
        channel = str(channel)
        self.send_channel_pos(channel)

    def switch_by_channel_number(self, channel):
        channel = str(channel)
        self.send_channel_pos(channel)

    #checks if spoken channel is in channel list (settings.json); if true fetch channel number
    def check_channel(self, channel):
        channel_wrong = channel
        LOG.info("channel ist: " + str(channel))
        channel = self.channels.get(channel, None)
        if channel != None:
            return channel
        else:
            self.speak_dialog('channel_error',{'channel': channel_wrong})

##Handlers
#basic handlers
    @intent_handler('channel.by.name.intent')
    def handle_channel_by_name(self, message):
        channel = message.data.get('channel')
        self.switch_by_channel_name(channel)

    @intent_handler('channel.by.number.intent')
    def handle_channel_by_name(self, message):
        utt = message.data.get('utterance')
        if "nummer" in utt:
            LOG.info("Inhalt von message: " + str(utt))
            channel = message.data.get('channel')
            self.switch_by_channel_number(channel)
        else:
            channel = message.data.get('channel')
            self.switch_by_channel_name(channel)


    @intent_handler('next_channel.intent')
    def handle_next_channel(self):
        keycode = "CHUP"
        self.send_keycode(keycode)

    @intent_handler('prev_channel.intent')
    def handle_prev_channel(self):
        keycode = "CHDOWN"
        self.send_keycode(keycode)

    @intent_handler('pos.intent')
    def handle_switch_to_pos(self, message):
        pos = message.data.get('pos_nr')
        pos = extract_number(pos); pos=str(int(pos))
        self.send_channel_pos(pos)

    @intent_handler('vol_up.intent')
    def handle_vol_up(self):
        keycode = "VOLUP"
        self.send_keycode(keycode)

    @intent_handler('vol_up_multi.intent')
    def handle_vol_up_multi(self, message):
        keycode = "VOLUP"
        steps = message.data.get('steps')
        steps = extract_number(steps); steps = int(steps)
        for i in range(0,steps):
            self.send_keycode(keycode)
            time.sleep(.1)
            i +=1

    @intent_handler('vol_down.intent')
    def handle_vol_down(self):
        keycode = "VOLDOWN"
        self.send_keycode(keycode)

    @intent_handler('vol_down_multi.intent')
    def handle_vol_down_multi(self, message):
        keycode = "VOLDOWN"
        steps = message.data.get('steps')
        steps = extract_number(steps); steps = int(steps)
        for i in range(0,steps):
            self.send_keycode(keycode)
            time.sleep(.1)
            i +=1

    @intent_handler('mute.intent')
    def handle_mute(self):
        keycode = "MUTE"
        self.send_keycode(keycode)

    @intent_handler('menu_leave.intent')
    def handle_menu_leave(self):
        keycode = "EXIT"
        self.send_keycode(keycode)

    @intent_handler('info.intent')
    def handle_info(self):
        keycode = "INFO"
        self.send_keycode(keycode)

    @intent_handler('poweroff.intent')
    def handle_poweroff(self):
        keycode = "POWEROFF"
        self.send_keycode(keycode)

#dialog handlers
    @intent_handler('channel_by_dialog.intent')
    def handle_channel_by_dialog(self, message):
        self.speak_dialog('howto.control.cursor')
        time.sleep(6)
        #move = self.explain_cursor_moves(self.translations)
        keycode = "CH_LIST"
        self.send_keycode(keycode)
        move = ""
        self.cursor_recursion(move)

    @intent_handler('program_guide_dialog.intent')
    def handle_program_guide(self):
        keycode = "GUIDE"
        self.send_keycode(keycode)
        move = self.explain_cursor_moves(self.translations)
        self.cursor_recursion(move)

    @intent_handler('source_dialog.intent')
    def handle_source(self):
        keycode = "SOURCE"
        self.send_keycode(keycode)
        move = self.explain_cursor_moves_source()
        self.cursor_recursion(move)

    @intent_handler('smarthub_dialog.intent')
    def handle_smarthub(self):
        keycode = "CONTENTS"
        self.send_keycode(keycode)
        move = self.explain_cursor_moves()
        self.cursor_recursion(move)

    @intent_handler('tools.intent')
    def handle_tools(self):
        keycode = "TOOLS"
        self.send_keycode(keycode)
        move = self.explain_cursor_moves()
        self.cursor_recursion(move)

#recording and playback handlers
    @intent_handler('pause.intent')
    def handle_timeshift_or_pause(self):
        keycode = "PAUSE"
        self.send_keycode(keycode)

    @intent_handler('play.intent')
    def handle_playing(self):
        keycode = "PLAY"
        self.send_keycode(keycode)

    @intent_handler('stop.intent')
    def handle_stop(self):
        keycode = "STOP"
        self.send_keycode(keycode)

    @intent_handler('record.intent')
    def handle_recording(self):
        keycode = "REC"
        self.send_keycode(keycode)

    @intent_handler('rewind.intent')
    def handle_rewind(self):
        keycode = "REWIND"
        self.send_keycode(keycode)

    @intent_handler('fastforward.intent')
    def handle_fastforward(self):
        keycode = "FF"
        self.send_keycode(keycode)

#source handlers
    @intent_handler('hdmi.intent')
    def handle_hdmi(self):
        keycode = "HDMI"
        self.send_keycode(keycode)

    @intent_handler('dtv.intent')
    def handle_dtv(self):
        keycode = "DTV"
        self.send_keycode(keycode)

    def stop(self):
        pass

def create_skill():
    return SamsungTVCtl()

