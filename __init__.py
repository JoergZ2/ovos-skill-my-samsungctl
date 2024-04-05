from mycroft import MycroftSkill, intent_handler
from mycroft.util import extract_number
from ovos_backend_client.api import DeviceApi
from ovos_workshop.skills import MycroftSkill
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.log import LOG
import sys
import os
import time
import samsungctl

DEFAULT_SETTINGS = {
    "tv": "192.168.178.91",
    "port": 55000,
    "placement": "Stube",
    "method": "legacy",
    "rc_name": "Ovos",
    "description_rc": "Beschreibung",
    "translations": {
        "hoch": "UP",
        "höher": "UP",
        "links": "LEFT",
        "rechts": "RIGHT",
        "rauf": "UP",
        "tiefer": "DOWN",
        "runter": "DOWN",
        "nehmen": "ENTER",
        "verlassen": "EXIT"
    },
    "stations": {
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

class SamsungTVCtl(MycroftSkill):
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
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        self.same_device = DeviceApi()
        self.info = self.same_device.uuid

    def on_settings_changed(self):
        self.curs_move_dict = {"nach links": "LEFT", "nach rechts": "RIGHT", "nach oben": "UP", "nach unten": "DOWN", "nehmen": "ENTER", "verlassen": "EXIT"}
        self.host = self.settings.get('tv')
        self.port = self.settings.get('port')
        self.placement = self.settings.get('placement')
        self.name_rc = self.settings.get('rc_name')
        self.method = self.settings.get('method')
        self.description_rc = self.settings.get('description_rc')
        self.translations = self.settings.get('translations')
        #self.trans = self.translations.split(',')
        #self.curs_move_dict = {self.trans[0]: 'LEFT', self.trans[1]: 'RIGHT', \
            #self.trans[2]: 'UP', self.trans[3]: 'DOWN', \
            #self.trans[4]: 'ENTER', self.trans[5]: 'EXIT'}
        self.stations = self.settings.get('stations')

        self.config = {"name": self.name_rc, "description": self.description_rc,\
            "id": "", "host": self.host, "port": self.port, "method": self.method,\
            "timeout": 0}

#Main functions
    def send_keycode(self, keycode):
        '''Standard function for sending keycodes'''
        keycode = "KEY_" + keycode.upper()
        try:
            with samsungctl.Remote(self.config) as remote:
                remote.control(keycode)
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
        '''Recursive function to handle cursor movements'''
        move = self.get_response('cursor_dummy',0)
        if move == None:
            keycode = "EXIT"
            self.send_keycode(keycode)
            return
        if move == self.trans[4]:
            keycode = "ENTER"
            self.send_keycode(keycode)
            return
        if move == self.trans[5]:
            keycode = "EXIT"
            self.send_keycode(keycode)
            return
        keycode = self.curs_move_dict[move]
        self.send_keycode(keycode)
        move = ""
        self.cursor_recursion(move)

    def cursor_recursion2(self, move):
        move = self.get_response()
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
                time.sleep(1)
                self.cursor_recursion2(move)
        else:
            self.speak_dialog('unknown.move', {'move': move})
            keycode = "EXIT"
            self.send_keycode(keycode)

    def switch_by_station_name(self, station):
        station = station.replace(' ','_').lower()
        station = self.check_station(station)
        station = str(station)
        self.send_channel_pos(station)

    #checks if spoken station is in station list (settings.json); if true fetch station number
    def check_station(self, station):
        station_wrong = station
        LOG.info("Station ist: " + str(station))
        station = self.stations.get(station, None)
        if station != None:
            return station
        else:
            self.speak_dialog('station_error',{'station': station_wrong})

##Handlers
#basic handlers
    @intent_handler('station.by.name.intent')
    def handle_station_by_name(self, message):
        station = message.data.get('station')
        self.switch_by_station_name(station)

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

    @intent_handler('vol_down.intent')
    def handle_vol_down(self):
        keycode = "VOLDOWN"
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
        self.cursor_recursion2(move)

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
    def handle_recording(self):
        keycode = "REWIND"
        self.send_keycode(keycode)

    @intent_handler('fastforward.intent')
    def handle_recording(self):
        keycode = "FF"
        self.send_keycode(keycode)

#source handlers
    @intent_handler('hdmi.intent')
    def handle_recording(self):
        keycode = "HDMI"
        self.send_keycode(keycode)

    @intent_handler('dtv.intent')
    def handle_recording(self):
        keycode = "DTV"
        self.send_keycode(keycode)

    def stop(self):
        pass

def create_skill():
    return SamsungTVCtl()

