
#################################
# Front panel navigation buttons
#################################

class NavButton(object):

    def __init__(self, draw_obj, nav_bar_top, fill, font):

        self.draw = draw_obj
        self.nav_bar_top = nav_bar_top
        self.font = font
        self.fill = fill

    def render_button(self, label, position):
        self.draw.text((position, self.nav_bar_top), label, self.fill, self.font)
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
