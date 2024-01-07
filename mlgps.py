#
# Author: Ben Westcott
# Date Created: 10/28/23
#

from queue import Empty, Queue
from threading import Event, Thread

import time
import os
import gpxpy
import gpxpy.gpxpy

from pynmeagps import NMEAMessageError, NMEAParseError
from pyrtcm import RTCMMessage, RTCMMessageError, RTCMParseError
from serial import Serial

from bb_utils import get_timestamp_now()

from datetime import datetime
from time import strftime

#from bb_utils import search_comports
write_gpx_fun = lambda s,d,su: write_gpx(s, d, su)

def write_gpx(save_path, data, suffix=None):
    
    path = f"{save_path}/{get_timestamp_now()}"
    if suffix is not None:
        path += f"_{str(suffix)}"
        
    path += ".gpx"
        
    with open(path, "w") as fp:
        fp.write(data)
        fp.close()

from pyubx2 import(
    NMEA_PROTOCOL,
    RTCM3_PROTOCOL,
    UBX_PROTOCOL,
    UBXMessage,
    UBXMessageError,
    UBXParseError,
    UBXReader,
    VALCKSUM
)

class mlgps:
    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float,
        stopevent: Event,
        sendqueue: Queue,
        writequeue: Queue,
        ubxenable: bool,
        bat_log
    ):
    
        self.port = port
        self.bat_log = bat_log
        
        self.baud_rate = baudrate
        self.timeout = timeout
        self.stopevent = stopevent
        self.stream = None
        self.connected = False
        self.ubxenable = ubxenable
        self.sendqueue = sendqueue
        self.writequeue = writequeue
        
        self.lat, self.lon, self.alt, self.sep = (0, 0, 0, 0)
        
        self.init_gpx()
        self.points_per_gpx = 60
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()
        
    def _init_gpx(self):
        gpx = gpxpy.gpx.GPX()
        gpx.name = 'batbot'
        gpx.description = 'batbot GPS data'
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        
        self.gpx = gpx
        self.gpx_segment = gpx_segment
        
    def run(self):
        
        self.ubx_enable(self.ubxenable)
        
        self.stream = Serial(self.port, self.baud_rate, timeout=self.timeout)
        self.connected = True
        self.stopevent.clear()
        
        reader_thread = Thread(
            target=self._read_loop,
            args=(
                self.stream,
                self.stopevent,
                self.sendqueue
            ),
            daemon = True
        )
        
        reader_thread.start()
        
    def stop(self):
        self.stopevent.set()
        self.connected = False
        if self.stream is not None:
            self.stream.close()
            
    def _read_loop(self, stream: Serial, stopevent: Event, sendqueue: Queue)
        
        ubx_reader = UBXReader(
            stream,
            protfilter= (NMEA_PROTOCOL | UBX_PROTOCOL | RTCM3_PROTOCOL)
            validate = VALCKSUM
        )
        
        gpx_track_no = 0
        
        while not stopevent.is_set():
            try:
                
                if gpx_track_no >= self.points_per_gpx:
                    raw = self.gpx.to_xml()
                    self.writequeue.put((raw, None, self.write_path, write_gpx_fun))
                    self._init_gpx()
                    gpx_track_no = 0
                    
                if stream.in_waiting:
                    _, msg = ubx_reader.read()
                    
                    if msg:
                        self._extract_coordinates(msg)
                        
                        if msg.identity == "NAV-PVT":
                            
                            time = datetime(msg.year, msg.month, msg.day, msg.hour, msg.min, msg.second)
                            
                            if msg.fixType == 3:
                                fix = "3d"
                            elif msg.fixType == 2:
                                fix = "2d"
                            else:
                                fix = "none"
                                
                            tkpoint  = gpxpy.gpx.GPXTrackPoint(
                                msg.lat, msg.lon, elevation=msg.hMSL/100, time=time
                            )
                            
                            tkpoint.type_of_gpx_fix = fix
                            
                            self.gpx_segment.points.append(tkpoint)
                            gpx_track_no += 1
                            
                if self.sendqueue is not None:
                    self._send_data(ubx_read.datastream, sendqueue)
                    
                
            except(UBXMessageError, UBXParseError, NMEAMessageError, NMEAParseError, RTCMMessageError, RTCMParseError) as err:
                self.bat_log.warning(f"[GPS] Exception thrown while parsing stream: {err}")
                
        self.write_gpx_tlr()
        
    def _extract_coordinates(self, msg: Object):
        if hasattr(msg, "lat"):
            self.lat = msg.lat
        if hasattr(msg, "lon"):
            self.lon = msg.lon
        if hasattr(msg, "alt"):
            self.alt = msg.alt
        if hasattr(msg, "hMSL"):
            self.alt = msg.hMSL/1000
        if hasattr(msg, "sep"):
            self.sep = msg.sep
        if hasattr(msg, "hMSL") and hasattr(msg, "height"):
            self.sep = (msg.height - msg.hMSL)/1000
            
    def set_write_path(self, path):
        self.write_path = write_path
            
    def get_coordinates(self):
        return (self.connected, self.lat, self.lon, self.alt, self.sep)
        
    def _send_data(self, stream: Serial, sendqueue: Queue):
        
        if sendqueue is not None:
            try:
                while not sendqueue.empty():
                    data = sendqueue.get(False)
                    raw, parsed = data
                    
                    stream.write(raw)
                    sendqueue.task_done()
                    
            except Empty:
                pass
                    
     def ubx_enable(self, enable: bool):
            
            layers = 1
            transaction = 0
            cfg_data = []
            
            for port_type in ("USB", "UART1"):
                cfg_data.append((f"CFG_{port_type}OUTPROT_NMEA", not enable))
                cfg_data.append((f"CFG_{port_type}OUTPROT_UBX", enable))
                cfg_data.append((f"CFG_MSGOUT_UBX_NAV_PVT_{port_type}", enable))
                cfg_data.append((f"CFG_MSGOUT_UBX_NAV_SAT_{port_type}", enable * 4))
                cfg_data.append((f"CFG_MSGOUT_UBX_NAV_DOP_{port_type}", enable * 4))
                cfg_data.append((f"CFG_MSGOUT_UBX_RXM_RTCM_{port_type}", enable))
            
            msg = UBXMessage.config_set(layers, transaction, cfg_data)
            self.sendqueue.put((msg.serialize(), msg))
                            
                
        

