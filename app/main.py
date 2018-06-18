
import kivy
kivy.require('1.11.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.label import Label


# icons location
THEMES_FOLDER = 'themes/default/'
# sidebar element list
ELEMENT_LIST = [('roadm_on.jpg', 'roadm_off.jpg', Label(text='ROADM')),
                ('amplifier_on.jpeg', 'amplifier_off.jpeg', Label(text='Amp')),
                ('transmitter_on.jpg', 'transmitter_off.jpg', Label(text='Trx')),
                ('fiber_on.jpg', 'fiber_off.jpg', Label(text='Fiber'))]

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
images = (image_on, image_off, obj)
'''
class SidebarIcon(ToggleButtonBehavior, Image):

    def __init__(self, images, **kwargs):
        super().__init__(**kwargs)
        self.img_on, self.img_off, self.el_type = images
        self.source = THEMES_FOLDER + self.img_off

    def on_state(self, widget, value):
        if value == 'down':
            self.source = THEMES_FOLDER + self.img_on
            root.ids['topo_map'].active_el = self.el_type
            print(root.ids['topo_map'].active_el.text)
        else:
            self.source = THEMES_FOLDER + self.img_off
            root.ids['topo_map'].active_el = None
            print(root.ids['topo_map'].active_el)


'''
Topology map with draggable elements
'''
class TopologyMap(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_el = ObjectProperty(None, allownone=True)


'''
Displays some mouseover info and application states
'''
class Statusbar(BoxLayout):
    pass


'''
Application instance with its config
'''
class Application(App):

    # TODO:
    # 1. default app config and its location
    # 1.1. main window size restriction
    # 1.2. icons theme location (THEMES_FOLDER)
    # 1.3. default working directory (PROJECTS_FOLDER)

    def build(self):
        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow


if __name__ == '__main__':
    Application().run()
