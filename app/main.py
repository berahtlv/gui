
import kivy
kivy.require('1.11.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.floatlayout import FloatLayout
#from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.behaviors.drag import DragBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.uix.label import Label

# TODO:
# 1. App setting panel with default config and its location
# 1.1. main window size restriction
# 1.2. icons theme location (THEMES_FOLDER)
# 1.3. default working directory (PROJECTS_FOLDER)

# basic app restrictions (SDL2 only!!!)
from kivy.config import Config
#Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', 800)
Config.set('graphics', 'height', 600)
Config.set('graphics', 'minimum_width', 700)
Config.set('graphics', 'minimum_height', 500)
# for dynamic access
#from kivy.core.window import Window
#Window.size = (500, 500)

# icons location
THEMES_FOLDER = 'themes/default/'


'''
Main application Window
'''
class MainWindow(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # workaround to get all MainWindow ids
        global root
        root = self

'''
Main application menu
'''
class Menubar(BoxLayout):
    pass


'''
Main toolbar for Menubar function shortcuts
'''
class Toolbar(BoxLayout):
    pass


'''
Sidebar with element list
'''
class Sidebar(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TODO: remove lazy workaround for icons centering
        self.add_widget(Widget())
        for el in ELEMENT_LIST:
            self.add_widget(SidebarIcon(el))
        self.add_widget(Widget())


'''
Sidebar element object
'''
class SidebarIcon(ToggleButtonBehavior, Image):

    def __init__(self, images, **kwargs):
        super().__init__(**kwargs)
        self.img_on, self.img_off, self.el_type = images
        self.source = THEMES_FOLDER + self.img_off

    def on_state(self, widget, value):
        if value == 'down':
            self.source = THEMES_FOLDER + self.img_on
            root.ids['topomap'].active_icon = self.el_type
        else:
            self.source = THEMES_FOLDER + self.img_off
            root.ids['topomap'].active_icon = ''


'''
Topology map with draggable elements
'''
class TopologyMap(RelativeLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_icon = StringProperty('')

    # TODO: create different objects
    #       create object with icon centered to the touch position
    def on_touch_up(self, touch):
        if self.active_icon and self.collide_point(*touch.pos):
            self.add_widget(TopomapIcon('roadm_off.png', pos=self.to_local(*touch.pos)))


'''
Draggable element
'''
class TopomapIcon(DragBehavior, Image):

    def __init__(self, image, **kwargs):
        super().__init__(**kwargs)
        self.source = THEMES_FOLDER + image

    def on_touch_move(self, touch):
        super().on_touch_move(touch)

        # allow movement only inside visible part of TopologyMap
        # TODO: resolve bug with window resizing
        dx, dy = self.parent.pos
        # X axis
        if (self.x + dx) < self.parent.x:
            self.x = self.parent.x - dx
        elif (self.x + self.width + dx) > (self.parent.x + self.parent.width):
            self.x = (self.parent.x + self.parent.width) - self.width - dx
        # Y axis
        if (self.y + dy) < self.parent.y:
            self.y = self.parent.y - dy
        elif (self.y + self.height + dy) > (self.parent.y + self.parent.height):
            self.y = (self.parent.y + self.parent.height) - self.height - dy


'''
Displays some mouseover info and application states
'''
class Statusbar(BoxLayout):
    pass


'''
Application instance with its config
'''
class Application(App):

    def build(self):
        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow


# sidebar element list
ELEMENT_LIST = (('roadm_on.png', 'roadm_off.png', 'ROADM'),
                ('amplifier_on.png', 'amplifier_off.png', 'AMP'),
                ('transceiver_on.png', 'transceiver_off.png', 'TRX'),
                ('fiber_on.png', 'fiber_off.png', 'FIBER'),
                ('fused_on.png', 'fused_off.png', 'FUSED'),
                )


if __name__ == '__main__':
    Application().run()
