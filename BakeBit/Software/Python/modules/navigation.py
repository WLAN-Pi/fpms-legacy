#################################
# Front panel navigation buttons
#################################
class NavButton(object):

    def __init__(self, g_vars, fill, font):
       
        self.nav_bar_top = g_vars.get('nav_bar_top')
        self.font = font
        self.fill = fill
        self.g_vars = g_vars
        
        # figure out key map in use
        self.key_map_name = g_vars.get('key_map')
        self.key_map = g_vars['key_mappings'][self.key_map_name]['key_labels']
        self.map_type = g_vars['key_mappings'][self.key_map_name]['type']
        
        self.back_pos = self.key_map['back']['position']
        self.back_label = self.key_map['back']['label']

        self.next_pos = self.key_map['next']['position']
        self.next_label = self.key_map['next']['label']

        self.down_pos = self.key_map['down']['position']
        self.down_label = self.key_map['down']['label']

    #######################################
    # Rendering of buttons on screen
    #######################################
    def render_button(self, label, position):
        # invert if using symbols
        if self.map_type == 'symbol':
            rect_fill = 255
            self.fill = 0
            self.g_vars['draw'].rectangle((position, self.nav_bar_top, position + 25, self.nav_bar_top + 15), outline=0, fill=rect_fill)
        
        self.g_vars['draw'].text((position, self.nav_bar_top), label, fill=self.fill, font=self.font)
        return


    def back(self, label="default", override=True):
        # use key map value if no value passed via method call
        if label=="default": label = self.back_label

        if override == True:
            # always over-ride label if we are using symbols
            if self.map_type=="symbol": label = self.back_label
        self.render_button(label, self.back_pos)
        return


    def next(self, label="default", override=True):
        # use key map value if no value passed via method call
        if label=="default": label = self.next_label
        if override == True:
            # always over-ride label if we are using symbols
            if self.map_type=="symbol": label = self.next_label
        self.render_button(label, self.next_pos)
        return


    def down(self, label="default", override=True):
        # use key map value if no value passed via method call
        if label=="default": label = self.down_label
        if override == True:
            # always over-ride label if we are using symbols
            if self.map_type=="symbol": label = self.down_label
        self.render_button(label, self.down_pos)
        return
    

