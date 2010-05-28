import os

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import glib
import gst


class MPRISService(dbus.service.Object):
    def __init__(self, object_path, player):
        bus_name = dbus.service.BusName('org.mpris.radioparadise', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, object_path)
        self.player = player

    @dbus.service.method(dbus_interface='org.freedesktop.MediaPlayer', out_signature='s')
    def GetIdentity(self):
        return 'RadioParadise 0.1'

    @dbus.service.method(dbus_interface='org.freedesktop.MediaPlayer', out_signature='(iiii)')
    def GetStatus(self):
        return 0, 0, 0, 1

    @dbus.service.method(dbus_interface='org.freedesktop.MediaPlayer', out_signature='a{sv}')
    def GetMetadata(self):
        return { 'artist': self.player.get_artist(),
                 'title': self.player.get_title(),
                 'album': '',
                 'time': 60 }

    @dbus.service.method(dbus_interface='org.freedesktop.MediaPlayer', out_signature='i')
    def PositionGet(self):
        return 30

    @dbus.service.signal(dbus_interface='org.freedesktop.MediaPlayer', signature='(iiii)')
    def StatusChange(self, status):
        pass

    @dbus.service.signal(dbus_interface='org.freedesktop.MediaPlayer', signature='a{sv}')
    def TrackChange(self, metadata):
        pass

class Player:
    def __init__(self, uri):
        self._artist = ''
        self._title = ''

        self.playbin = gst.element_factory_make('playbin')
        self.playbin.props.uri = uri

        bus = self.playbin.get_bus()
        bus.connect('message', self._on_bus_message)
        bus.add_signal_watch()

    def _on_bus_message(self, bus, message, *args):
        if message.type != gst.MESSAGE_TAG:
            return
        x = []
        for key in message.structure.keys():
            x.append('%s: %s' % (key, message.structure[key]))
        if message.src.get_name().startswith('icydemux'):
            print ', '.join(x)
            title = message.structure['title']
            self._title, self._artist = title.split(' - ', 1) 

    def get_artist(self):
        return self._artist

    def get_title(self):
        return self._title

    def run(self):
        self.playbin.set_state(gst.STATE_PLAYING)

        loop = glib.MainLoop()
        loop.run()

def main():
    DBusGMainLoop(set_as_default=True)

    URI = 'http://scfire-mtc-aa02.stream.aol.com:80/stream/1048'


    # Disable proxy by default
    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']

    p = Player(URI)
    service = MPRISService('/Player', p)
    p.run()

if __name__ == '__main__':
    main()
