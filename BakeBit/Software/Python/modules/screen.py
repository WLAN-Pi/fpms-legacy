
#################################
# Screen functions
#################################

class Screen(object):

    def __init__(self, g_vars):
        pass

    def clear_display(self, g_vars):

        '''
        Paint display black prior to painting new page
        '''

        # Draw a black filled box to clear the display.
        g_vars['draw'].rectangle((0, 0, g_vars['width'], g_vars['height']), outline=0, fill=0)

        return

