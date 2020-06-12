import time
import os.path
import subprocess
import bakebit_128_64_oled as oled

from modules.pages.simpletable import SimpleTable
from modules.constants import (
    KISMET_CTL_FILE,
    BETTERCAP_CTL_FILE,
    PROFILER_CTL_FILE,
)


class App(object):

    def __init__(self, g_vars):
       
        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

    def kismet_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Kismet processes
        '''

        kismet_ctl_file = KISMET_CTL_FILE

        # check resource is available
        if not os.path.isfile(kismet_ctl_file):
            self.simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(
                kismet_ctl_file), back_button_req=1)
            g_vars['display_state'] = 'page'
            return
        
        if action == "status":
            # check kismet status & return text
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(kismet_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Status failed! {}'.format(output)

        elif action == "start":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(kismet_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Start failed! {}'.format(output)

        elif action == "stop":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(kismet_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Stop failed! {}'.format(output)

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
        g_vars['display_state'] = 'page'
        return True


    def kismet_status(self, g_vars):
        self.kismet_ctl(g_vars, action="status")
        return


    def kismet_stop(self, g_vars):
        self.kismet_ctl(g_vars, action="stop")
        return


    def kismet_start(self, g_vars):
        self.kismet_ctl(g_vars, action="start")
        return


    def bettercap_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Kismet processes
        '''
        bettercap_ctl_file = BETTERCAP_CTL_FILE

        # check resource is available
        if not os.path.isfile(bettercap_ctl_file):
            self.simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(
                bettercap_ctl_file), back_button_req=1)
            g_vars['display_state'] = 'page'
            return

        if action == "status":
            # check bettercap status & return text
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Status failed! {}'.format(output)

        elif action == "start":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Start failed! {}'.format(output)

        elif action == "stop":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(bettercap_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Stop failed! {}'.format(output)

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
        g_vars['display_state'] = 'page'
        return True


    def bettercap_status(self, g_vars):
        self.bettercap_ctl(g_vars, action="status")
        return


    def bettercap_stop(self, g_vars):
        self.bettercap_ctl(g_vars, action="stop")
        return


    def bettercap_start(self, g_vars):
        self.bettercap_ctl(g_vars, action="start")
        return

    def profiler_running(self):
        try:
            # this cmd fails if process not active
            cmd = "systemctl is-active --quiet profiler.service"
            cmd_output = subprocess.check_output(cmd, shell=True).decode()
            return True
        except subprocess.CalledProcessError as exc:
            return False
                
    def profiler_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Profiler processe
        '''
        # check resource is available
        try:
            # this cmd fails if service no installed
            cmd = "systemctl is-enabled profiler.service"
            cmd_output = subprocess.check_output(cmd, shell=True).decode()
        except:
            # cmd failed, so profiler service not installed
            self.simple_table_obj. display_dialog_msg(g_vars, 'not available: {}'.format(
                profiler_ctl_file), back_button_req=1)
            g_vars['display_state'] = 'page'
            return
        
        dialog_msg = "Unset"
        item_list = []

        # get profiler process status
        # (no check for cached result as need to re-evaluate 
        # on each 1 sec main loop cycle)
        if action == "status":
            # check profiler status & return text
            if self.profiler_running():
                item_list = ['Profiler active']
            else:
                item_list = ['Profiler not active']

            self.simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=1,
                                title='Profiler Status')
            g_vars['display_state'] = 'page'
            return True

        # if we're been round this loop before, 
        # results treated as cached to prevent re-evaluating
        # and re-painting 
        if g_vars['result_cache'] == True:
           return True

        if action == "start":
            # disable keys while we do this
            g_vars['disable_keys'] = True

            if self.profiler_running():
                dialog_msg = 'Already running!'
            else:
                try:
                    cmd = "systemctl start profiler.service"
                    cmd_output = subprocess.check_output(cmd, shell=True).decode()
                    dialog_msg = "Started."
                except subprocess.CalledProcessError as exc:
                    dialog_msg = 'Start failed!'
                
                # signal that result is cached (stops re-painting screen)
                g_vars['result_cache'] = True

            # re-enable keys
            g_vars['disable_keys'] = False

        elif action == "start_no11r":
            pass

        elif action == "stop":
            # disable keys while we do this
            g_vars['disable_keys'] = True

            if not self.profiler_running():
                dialog_msg = 'Already stopped!'
            else:
                try:
                    cmd = "systemctl stop profiler.service"
                    cmd_output = subprocess.check_output(cmd, shell=True).decode()
                    dialog_msg = "Stopped"
                except subprocess.CalledProcessError as exc:
                    dialog_msg = 'Stop failed!'
                
                # signal that result is cached (stops re-painting screen)
                g_vars['result_cache'] = True

            # re-enable keys
            g_vars['disable_keys'] = False

        elif action == "purge":
            pass

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req=1)
        g_vars['display_state'] = 'page'
        return True


    def profiler_status(self, g_vars):
        self.profiler_ctl(g_vars, action="status")
        return


    def profiler_stop(self, g_vars):
        self.profiler_ctl(g_vars, action="stop")
        return


    def profiler_start(self, g_vars):
        self.profiler_ctl(g_vars, action="start")
        return


    def profiler_start_no11r(self, g_vars):
        self.profiler_ctl(g_vars, action="start_no11r")
        return


    def profiler_purge(self, g_vars):
        self.profiler_ctl(g_vars, action="purge")
        return