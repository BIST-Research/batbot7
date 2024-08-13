import numpy as np
import time
import os
import numpy as np
from scipy import signal
from datetime import datetime
import m4
import yaml

from threading import Thread

from bb_utils import get_timestamp_now

write_npy_fun = lambda s, d, su: write_npy(s, d, su)


def write_npy(save_path, data, suffix=None):
    path = f"{save_path}/{get_timestamp_now()}"
    if suffix is not None:
        path += f"_{str(suffix)}"

    path += ".npy"

    with open(path, "wb") as fd:
        np.save(fd, np.array(data))
        fd.close()


class DataThread(Thread):
    def __init__(self, write_queue, exit_cond):
        Thread.__init__(self)
        self.q = write_queue
        self.exit_cond = exit_cond

    def run(self):
        while True:
            if self.exit_cond() and self.q.empty():
                break

            if not self.q.empty():
                data, data_suffix, save_path, write_fun = self.q.get()

                write_fun(save_path, data, data_suffix)
                self.q.task_done()

            else:
                time.sleep(0.01)


class DataController:
    def __init__(self, conf_name, bat_log):
        self.bat_log = bat_log
        conf = None
        with open(conf_name) as fd:
            conf = yaml.safe_load(fd)
            fd.close()

        if conf is None:
            self.bat_log.critical(
                f"Please check if your configuration file exists and is parseable!"
            )
            exit()

        self.bat_log.info(f"[Data] Found {conf_name}, loading settings...")

        self.sonar_boards = conf["sonar_boards"]
        self.sonar_baud = conf["sonar_baud"]
        self.do_plot = conf["do_plot"]

        self.sonar_plot_book = conf["sonar_plot"]
        self.gps_book = conf["gps"]

        parent_directory = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = parent_directory + f"/{str(conf['data_directory'])}"

        if not os.path.exists(self.data_dir):
            bat_log.debug(f"[Data] Creating root data path... ")
            os.makedirs(self.data_dir)

    def create_run_dir(self, suffix=None, prefix=None):
        run_dir = ""
        if prefix is not None:
            run_dir += f"{prefix}_"

        run_dir = f"{get_timestamp_now()}"
        if suffix is not None:
            run_dir += f"_{str(suffix)}"

        os.makedirs(self.data_dir + "/" + run_dir)
        return run_dir

    def get_sonar_boards(self):
        return self.sonar_boards

    def get_sonar_baud(self):
        return self.sonar_baud

    def get_sonar_plot_book(self):
        return self.sonar_plot_book

    def get_gps_book(self):
        return self.gps_book

    def get_data_directory(self):
        return self.data_dir


if __name__ == "__main__":
    conf_name = "bat_conf.yaml"
    bat_log = bb_log.get_log()

    data_controller = DataController(conf_name, bat_log)
    dir1 = data_controller.create_run_dir()

    dump_list = []
    for x in range(0, 10000):
        dump_list.append(0xF3)

    data_controller.dump_as_npy(dir1, dump_list)

    dir2 = data_controller.create_run_dir(suffix="test")

    data_controller.dump_as_npy(dir2, dump_list, suffix="test")
