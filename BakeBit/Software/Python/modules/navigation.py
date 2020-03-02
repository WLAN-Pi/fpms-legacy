
#################################
# Front panel navigation buttons
#################################

class NavButton(object):

    def __init__(self, g_vars, fill, font):
       
        self.nav_bar_top = g_vars.get('nav_bar_top')
        self.font = font
        self.fill = fill
        self.g_vars = g_vars

    def render_button(self, label, position):
        self.g_vars['draw'].text((position, self.nav_bar_top), label, fill=self.fill, font=self.font)
        return


    def back(self, label="Back", position=100):
        self.render_button(label, position)
        return


    def next(self, label="Next", position=50):
        self.render_button(label, position)
        return


    def down(self, label="Down", position=0):
        self.render_button(label, position)
        return
