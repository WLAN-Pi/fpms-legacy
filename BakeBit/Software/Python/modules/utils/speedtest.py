import subprocess

from modules.simpletable import * 

class Speedtest(object):

    def __init__(self, g_vars):
       
        # create simple table object to show dialog & results on display 
        self.simple_table_obj = SimpleTable(g_vars)

    def show_speedtest(self, g_vars):
        '''
        Run speedtest.net speed test and format output to fit the OLED screen
        ( *** Note that speedtest_status set back to False in menu_right() *** )
        '''
        # Has speedtest been run already?
        if g_vars['speedtest_status'] == False:

            # ignore any more key presses as this could cause us issues
            g_vars['disable_keys'] = True

            self.simple_table_obj.display_dialog_msg(g_vars, 'Running Speedtest. Please wait.', back_button_req=0)

            speedtest_info = []
            speedtest_cmd = "speedtest | egrep -w \"Testing from|Download|Upload\" | sed -r 's/Testing from.*?\(/My IP: /g; s/\)\.\.\.//g; s/Download/D/g; s/Upload/U/g; s/bit\/s/bps/g'"

            try:
                speedtest_output = subprocess.check_output(speedtest_cmd, shell=True).decode()
                speedtest_info = speedtest_output.split('\n')
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                error = ["Err: Speedtest error", output]
                self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
                return

            if len(speedtest_info) == 0:
                speedtest_info.append("No output sorry")

            # chop down output to fit up to 2 lines on display
            g_vars['speedtest_result_text'] = []

            for n in speedtest_info:
                g_vars['speedtest_result_text'].append(n[0:20])
                if len(n) > 20:
                    g_vars['speedtest_result_text'].append(n[20:40])

            g_vars['speedtest_status'] = True

        # re-enable front panel keys
        g_vars['disable_keys'] = False

        self.simple_table_obj.display_simple_table(g_vars, g_vars['speedtest_result_text'], back_button_req=1, title='--Speedtest--')