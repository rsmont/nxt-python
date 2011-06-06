# nxt.locator module -- Locate LEGO Minstorms NXT bricks via USB or Bluetooth
# Copyright (C) 2006, 2007  Douglas P Lau
# Copyright (C) 2009  Marcus Wanner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import traceback

class BrickNotFoundError(Exception):
    pass

class NoBackendError(Exception):
    pass

class Method():
    """Used to indicate which comm backends should be tried by find_bricks/
find_one_brick. Any or all can be selected."""
    def __init__(self, usb=True, bluetooth=True, fantomusb=False, fantombt=False):
        #new method options MUST default to False!
        self.usb = usb
        self.bluetooth = bluetooth
        if fantomusb or fantombt:
            self.fantom = True
        self.fantomusb = fantomusb
        self.fantombt = fantombt

def find_bricks(host=None, name=None, silent=False, method=Method()):
    """Used by find_one_brick to look for bricks ***ADVANCED USERS ONLY***"""
    methods_available = 0

    if method.usb:
        try:
            import usbsock
            methods_available += 1
            socks = usbsock.find_bricks(host, name)
            for s in socks:
                yield s
        except ImportError:
            import sys
            if not silent: print >>sys.stderr, "USB module unavailable, not searching there"
    
    if method.bluetooth:
        try:
            import bluesock
            methods_available += 1
            try:
                socks = bluesock.find_bricks(host, name)
                for s in socks:
                    yield s
            except (bluesock.bluetooth.BluetoothError, IOError): #for cases such as no adapter, bluetooth throws IOError, not BluetoothError
                pass
        except ImportError:
            import sys
            if not silent: print >>sys.stderr, "Bluetooth module unavailable, not searching there"
    
    if method.fantom:
        try:
            import fantomsock
            methods_available += 1
            if method.fantomusb:
                usbsocks = fantomsock.find_bricks(host, name, False)
                for s in usbsocks:
                    yield s
            if method.fantombt:
                btsocks = fantomsock.find_bricks(host, name, True)
                for s in btsocks:
                    yield s
        except ImportError:
            import sys
            if not silent: print >>sys.stderr, "Fantom module unavailable, not searching there"
    
    if methods_available == 0:
        raise NoBackendError("No selected backends are available! Did you install the comm modules?")


def find_one_brick(host=None, name=None, silent=False, strict=True, debug=False, method=Method()):
    """Use to find one brick. After it returns a usbsock object or a bluesock
object, it automatically connects to it. The host and name args limit
the search to a given MAC or brick name. Set silent to True to stop
nxt-python from printing anything during the search. This function by default 
automatically checks to see if the brick found has the correct host/name 
(if either are provided) and will not return a brick which doesn't
match. This can be disabled (so the function returns any brick which
can be connected to and provides a valid reply to get_device_info()) by
passing strict=False. This will, however, still tell the USB/BT backends to 
only look for devices which match the args provided."""
    if debug and silent:
        silent=False
        print "silent and debug can't both be set; giving debug priority"

    for s in find_bricks(host, name, silent, method):
        try:
            if host and 'host' in dir(s) and s.host != host:
                if debug:
                    print "Warning: the brick found does not match the host provided (s.host)."
                if strict: continue
            b = s.connect()
            info = b.get_device_info()
            if host and info[1] != host:
                if debug:
                    print "Warning: the brick found does not match the host provided (get_device_info)."
                if strict:
                    s.close()
                    continue
            if name and info[0].strip('\0') != name:
                if debug:
                    print "Warning; the brick found does not match the name provided."
                if strict:
                    s.close()
                    continue
            return b
        except:
            if debug:
                traceback.print_exc()
                print "Failed to connect to possible brick"
    raise BrickNotFoundError


def server_brick(host, port = 2727):
    import ipsock
    sock = ipsock.IpSock(host, port)
    return sock.connect()
