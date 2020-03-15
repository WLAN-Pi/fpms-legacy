import time
import os.path
import subprocess
import bakebit_128_64_oled as oled

from modules.pages.simpletable import *

class App(object):

    def __init__(self, g_vars):
       
        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

    def kismet_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Kismet processes
        '''
        kismet_ctl_file = g_vars['kismet_ctl_file']

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
        bettercap_ctl_file = g_vars['bettercap_ctl_file']

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


    def profiler_ctl(self, g_vars, action="status"):
        '''
        Function to start/stop and get status of Profiler processe
        '''
        profiler_ctl_file = g_vars['profiler_ctl_file']

        # check resource is available
        if not os.path.isfile(profiler_ctl_file):
            self.simple_table_obj. display_dialog_msg(g_vars, 'not available: {}'.format(
                profiler_ctl_file), back_button_req=1)
            g_vars['display_state'] = 'page'
            return

        if action == "status":
            # check profiler status & return text
            try:
                status_file_content = subprocess.check_output(
                    "{} {}".format(profiler_ctl_file, action), shell=True).decode()
                item_list = status_file_content.splitlines()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                item_list = ['Status failed!', str(output)]

            self.simple_table_obj.display_simple_table(g_vars, item_list, back_button_req=1,
                                title='Profiler Status')
            g_vars['display_state'] = 'page'
            return True

        elif action == "start":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(profiler_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Start failed! {}'.format(output)

        elif action == "start_no11r":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(profiler_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Start failed! {}'.format(output)

        elif action == "stop":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(profiler_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Stop failed! {}'.format(output)

        elif action == "purge":
            try:
                dialog_msg = subprocess.check_output(
                    "{} {}".format(profiler_ctl_file, action), shell=True).decode()
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                dialog_msg = 'Report purge failed! {}'.format(output)

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