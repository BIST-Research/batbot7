""" bb_gps2
Brief: this is the gps object used by the batbot, this 
can use NTRIP for RTK and run baseless.
Author: Mason Lopez
Date: 2/7/2024

Documentation on zed fp9: https://cdn.sparkfun.com/assets/f/7/4/3/5/PM-15136.pdf

finding basestations: http://www.rtk2go.com:2101/SNIP::STATUS#single

    """
from serial import Serial
from pyubx2 import UBXReader, UBXMessage

# for debugging create logging module
import logging
logging.basicConfig(level=logging.DEBUG)

# for logging gps points
import gpxpy
from gpxpy.gpx import GPXTrackSegment,GPXTrackPoint, GPX


from datetime import datetime
from time import sleep,strftime
from threading import Thread, Event

import pyrtcm.rtcmmessage

import numpy as np
from queue import Queue, Empty

# for NTRIP corrections
from pygnssutils import GNSSNTRIPClient, VERBOSITY_DEBUG,VERBOSITY_HIGH,VERBOSITY_LOW,VERBOSITY_MEDIUM
    
    
class bb_gps2():
    def __init__(self, serial: Serial = Serial(),
                 ntripuser:str=None,
                 mountpoint:str="VTTI_SR_RTCM3",
                 ntripserver:str="RTK2go.com",
                 ntripport:int=2101,
                 ntrippassword:str="none",
                 ) -> None:
        self.stop_event = Event()
        self.serial = serial
        
        # for ntrip client
        self.ntripuser=ntripuser
        self.ntrippassword=ntrippassword
        self.mountpoint=mountpoint
        self.ntripport=ntripport
        self.ntripserver=ntripserver
        self.ntripclient = GNSSNTRIPClient(verbosity = VERBOSITY_DEBUG,logtofile=True)
        
        # ublox message parser
        self.ubr = UBXReader(self.serial)
        
        # tracking points of gps using 
        self.gpx = GPX()
        self.gpx.name = "Batbot 7 GPS"
        self.gpx_segment = GPXTrackSegment()
        self.gpx.tracks.append(self.gpx_segment)
        self.gpx_point_count = 0
        self.gpx_point_save_threshold = 60
        self.gpx_file_count = 0
        
        self.total_coords_count = 0
        self.last_coord = [0,0]


    
    def connect_Serial(self,serial:Serial):
        self.serial = serial
        
    def connection_status(self)->bool:
        return self.serial.is_open
    
    def disconnect_serial(self):
        try:
            self.serial.close()
        except:
            pass
        
    def get_num_coodinates(self)->int:
        return self.total_coords_count
        
    
    def run(self, dir:str = "",do_print:bool = False):
        self.dump_dir = dir
        
        if not self.set_ubx_only_output(True):
            exit("Failed to set ubx output to only ubx")
        
        if not self.set_ubx_only_NAV_PVT(True):
            exit("Failed to set ubx output to NAT PVT")
      
        if not self.set_ubx_rtcm(True):
            exit("Failed to set ubx RTCM inputs")
        
        if not self.set_message_rate(500):
            exit("Failed to set message rate")
        
        logging.debug("Success setting UBX parameters")
        print("Success setting UBX parameters")
        

        # corrections for creating 
        ntrip_corrections = Queue()
        using_ntrip = False
        
        if self.ntripuser is not None:
            logging.debug(f"Trying NTRIP connection on mountpoint: {self.mountpoint}, user: {self.ntripuser}")
            self.ntripclient.run(
                server=self.ntripserver, 
                port=self.ntripport, 
                mountpoint=self.mountpoint, 
                ntripuser=self.ntripuser, 
                ntrippassword=self.ntrippassword,
                logtofile=True,
                verbosity = VERBOSITY_DEBUG,
                output=ntrip_corrections)
            
            
                # if not ntrip_corrections.empty():
            try:
                msg = ntrip_corrections.get(timeout=2)
                if msg and isinstance(msg[1],pyrtcm.RTCMMessage):
                    logging.debug(f"Success connecting to mountpoint: {self.mountpoint}")
                    using_ntrip = True
            except Empty:
                logging.error(f"Failed to connect to mountpoint: {self.mountpoint}")
                
    
        else:
            logging.debug("No NTRIP mountpoint given, running without RTCM")
            
        
        # loop where data is collected, saved and RTCM is sent
        while not self.stop_event.is_set():
            
            # if we get NTRIP corrections send it 
            if not ntrip_corrections.empty():
                msg = ntrip_corrections.get()
                raw,_ = msg
                self.serial.write(raw)
                if do_print:
                    print("Sent NTRIP Corrections")

            # poll serial for messages
            (_,msg) = self.ubr.read()
            if msg:
                time = datetime(msg.year,msg.month,msg.day,msg.hour,msg.min,msg.second)
                if do_print:
                    print(f"lat: {msg.lat} long: {msg.lon} identity: {msg.identity} time { time.strftime('%Y%m%d_%H%M%S') }")
                track_point = GPXTrackPoint(latitude=msg.lat,
                                            longitude=msg.lon,
                                            elevation=msg.hMSL/100,
                                            time=time,
                                            position_dilution=msg.pDOP)
                
                self.gpx_segment.points.append(track_point)
                self.total_coords_count +=1
                self.last_coord[0] = msg.lat
                self.last_coord[1] = msg.lon

                self.save_gpx_data()

        self.save_gpx_data()
            
    def save_gpx_data(self)->None:
        if self.gpx_point_count >= self.gpx_point_save_threshold or (self.stop_event.is_set() and self.gpx_point_count > 1):
            xml = self.gpx.to_xml()
            filename = "GPS_"+strftime("%Y%m%d_%H%M%S")+"_part"+str(self.gpx_file_count)+".gpx"
            
            with open(self.dump_dir+"/"+filename,"w") as file:
                file.write(xml)

            self.gpx_file_count+=1
            self.gpx_point_count = 0

            # reset the segment
            self.gpx = GPX()
            self.gpx.name = "Batbot 7 GPS"
            self.gpx_segment = GPXTrackSegment()
            self.gpx.tracks.append(self.gpx_segment)

        self.gpx_point_count+=1
        
    
        
    def stop(self):
        self.stop_event.set()
        logging.debug("Stopping gps collections")
    
    
    def set_message_rate(self,refresh_rate_ms:np.uint16)->bool:
        cfg_data = []
        
        cfg_data.append(("CFG_RATE_MEAS", refresh_rate_ms))
        
        msg = UBXMessage.config_set(1,0,cfg_data)
        
        self.serial.write(msg.serialize())
        self.serial.flush()
        return self.check_for_ubx_ack(f"CFG_RATE_MEAS {refresh_rate_ms}ms")
    
    def set_ubx_only_output(self,enable:bool)->bool:
        cfg_data = []
        
        cfg_data.append(("CFG_USBOUTPROT_NMEA", not enable))
        cfg_data.append(("CFG_USBOUTPROT_UBX", enable))
        cfg_data.append(("CFG_USBOUTPROT_RTCM3X", enable))
        
        msg = UBXMessage.config_set(1,0,cfg_data)
        
        self.serial.write(msg.serialize())
        self.serial.flush()
        return self.check_for_ubx_ack(f"CFG_USBOUTPROT_NMEA {not enable},CFG_USBOUTPROT_UBX {enable}")
    
    def set_ubx_only_NAV_PVT(self,enable:bool)->bool:
        cfg_data = []
        
        cfg_data.append(("CFG_MSGOUT_UBX_NAV_PVT_USB",enable))
        msg = UBXMessage.config_set(1,0,cfg_data)
        
        self.serial.write(msg.serialize())
        self.serial.flush()
        return self.check_for_ubx_ack(f"CFG_MSGOUT_UBX_NAV_PVT_USB {enable}")
    
    def set_ubx_rtcm(self,enable:bool)->bool:
        cfg_data = []
        
        cfg_data.append(("CFG_USBINPROT_RTCM3X",enable))
        cfg_data.append(("CFG_USBOUTPROT_RTCM3X",enable))
        msg = UBXMessage.config_set(1,0,cfg_data)
        
        self.serial.write(msg.serialize())
        self.serial.flush()
        return self.check_for_ubx_ack(f"CFG_USBINPROT_RTCM3X {enable}")

    def set_serial_str(self)->bool:
        cfg_data = []
        
        cfg_data.append(("CFG_USB_SERIAL_NO_STR0","BB7_GPS0".encode()))
        msg = UBXMessage.config_set(4,0,cfg_data)
        
        self.serial.write(msg.serialize())
        self.serial.flush()
        return self.check_for_ubx_ack(f"CFG_USB_SERIAL_NO_STR0")
    

    
    def check_for_ubx_ack(self, msg_to_ack:str)->bool:
        for i in range(5):
            _,msg = self.ubr.read()
            if not msg or not hasattr(msg,"identity"):
                continue
            if msg.identity == "ACK-ACK":
                logging.debug(f"Success: UBX ACK'D '{msg_to_ack}'")
                return True
            elif msg.identity == "ACK-NACK":
                logging.debug(f"Error: UBX NACK'D '{msg_to_ack}'")
                return False
                
        logging.debug(f"Error: UBX did not ACK or NACK: '{msg_to_ack}'")
        return False
    
        
    
    
if __name__ == "__main__":
    
    print("Starting batbot gps ")
    
    gps = bb_gps2(Serial('/dev/tty.usbmodemBB7_GPS01', 9600, timeout=3))
    # gps = bb_gps2(Serial('/dev/tty.usbmodem14101', 9600, timeout=3),
    #               ntripuser="masonlopez@vt.com")
    
    # gps.run("experiment1")
    # gps_thread = Thread(target=gps.run,args=("Experiments1",None))


    # gps_thread.start()


    msg = input("press any key to stop \n\n")
    print("Ending collections")

    # gps.stop_event.set()

        
    
    


