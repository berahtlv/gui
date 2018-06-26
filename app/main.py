
import kivy
kivy.require('1.11.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.behaviors.drag import DragBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ObjectProperty, OptionProperty, ListProperty
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle

import networkx as nx
import random

# TODO:
# 1. App setting panel with default config and its location
# 1.1. main window size restriction
# 1.2. icons theme location (THEMES_FOLDER)
# 1.3. default working directory (PROJECTS_FOLDER)
# 1.4. window colortheme (hardcoded in .kv)

# basic app restrictions (SDL2 only!!!)
from kivy.config import Config
Config.set('graphics', 'width', 1024)
Config.set('graphics', 'height', 768)
Config.set('graphics', 'minimum_width', 800)
Config.set('graphics', 'minimum_height', 550)

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

        self.add_widget(Widget())
        for el in ELEMENT_LIST:
            self.add_widget(SidebarIcon(el))
        self.add_widget(Widget(size_hint=(1, None), height=50))
        for func in FUNCTION_LIST:
            self.add_widget(SidebarIcon(func))
        self.add_widget(Widget())


'''
Sidebar element object
'''
class SidebarIcon(ToggleButtonBehavior, Image):

    def __init__(self, el_info, **kwargs):
        super().__init__(**kwargs)
        self.img_on, self.img_off, self.el_type, self.el_descr = el_info
        self.source = THEMES_FOLDER + self.img_off


    def on_state(self, widget, value):
        if value == 'down':
            self.source = THEMES_FOLDER + self.img_on
            root.ids['topomap'].active_icon = self
        else:
            self.source = THEMES_FOLDER + self.img_off
            # drops connectable element list and active icon when unselected
            root.ids['topomap'].active_icon = None
            root.ids['topomap'].connectable_el = []


'''
Topology map with draggable elements
'''
class TopologyMap(RelativeLayout):

    active_icon = ObjectProperty(None, allownone=True)
    connectable_el = ListProperty([])
    topology = ObjectProperty(nx.Graph())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def on_touch_down(self, touch):
        if self.active_icon and self.collide_point(*touch.pos):
            if not self.active_icon.el_type in ['REMOVE', 'CONNECTION']:
                new_element = TopomapIcon(self.active_icon,
                                          pos=self.to_local(*(i - 25 for i in touch.pos))
                                          )
                self.topology.add_node(new_element)
                self.add_widget(new_element)

                return True

        return super().on_touch_down(touch)


    # connects topomap icons based on accumulated connectable_el objects
    def _connect_el(self):
        # checks if connection between nodes already exists
        if not self.topology.has_edge(*self.connectable_el):
            a, b = [(i.pos, i.size) for i in self.connectable_el]
            pos_A = (a[0][0] + a[1][0]/2, a[0][1] + a[1][1]/2)
            pos_B = (b[0][0] + b[1][0]/2, b[0][1] + b[1][1]/2)

            # adds graphical representation
            connection = TopomapConnect(pos_A + pos_B)
            self.add_widget(connection, canvas='before')
            # updates topology
            self.topology.add_edge(*self.connectable_el, obj=connection)

        # unselects sidebar icon, active_icon and connectable_el are dropped in on_state event
        self.active_icon.state = 'normal'


'''
Draggable element
'''
class TopomapIcon(DragBehavior, Image):

    el_type = StringProperty('')
    el_id = StringProperty('')

    def __init__(self, info_obj, **kwargs):
        super().__init__(**kwargs)
        self.img_off = info_obj.img_off
        self.img_on = info_obj.img_on
        self.el_type = info_obj.el_type
        self.source = THEMES_FOLDER + self.img_off
        self.el_id = 'ID'+''.join((str(random.randrange(0,9)) for i in range(3)))


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.source = THEMES_FOLDER + self.img_on

            # removes element and all its connections from map and topology graph
            if getattr(self.parent.active_icon, 'el_type', None) == 'REMOVE':
                if self.parent.topology.edges(self):
                    for u, v, c in self.parent.topology.edges(self, data=True):
                        self.parent.remove_widget(c['obj'])

                self.parent.topology.remove_node(self)
                self.parent.remove_widget(self)

                return True

            # create connection between topomap icons
            if getattr(self.parent.active_icon, 'el_type', None) == 'CONNECTION':
                if not self in self.parent.connectable_el:
                    self.parent.connectable_el.append(self)

                if len(self.parent.connectable_el) == 2:
                    self.parent._connect_el()

                return True

        return super().on_touch_down(touch)


    def on_touch_up(self, touch):
        # w/o collision, mouse can be released outside of collision region
        # TODO: maybe improve for collision with mouse_pos ???
        self.source = THEMES_FOLDER + self.img_off

        return super().on_touch_up(touch)


    def on_pos(self, instance, value):
        if self.parent:
            # updates connection lines
            if self.parent.topology.edges(self):
                for u, v, c in self.parent.topology.edges(self, data=True):
                    c['obj']._update(u, v)

            # allows movement only inside visible part of TopologyMap
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
Connection of draggable elements
'''
class TopomapConnect(Widget):

    conn_dir = OptionProperty('bidir', options=['bidir', 'unidir'])
    conn_color = ListProperty([])
    conn_points = ListProperty([])

    def __init__(self, coord, **kwargs):
        super().__init__(**kwargs)

        self.size = (abs(coord[0] - coord[2]),
                     abs(coord[1] - coord[3])
                     )
        self.pos = (min(coord[0], coord[2]),
                    min(coord[1], coord[3])
                    )
        self.conn_color = [0, 0.6, 0, 1]
        self.conn_points = coord


    # updates connection properties after TopomapIcon movement
    def _update(self, el_A, el_B):
        self.conn_points = (el_A.pos[0] + el_A.size[0]/2,
                            el_A.pos[1] + el_A.size[1]/2,
                            el_B.pos[0] + el_B.size[0]/2,
                            el_B.pos[1] + el_B.size[1]/2
                            )
        self.pos = (min(self.conn_points[0], self.conn_points[2]),
                    min(self.conn_points[1], self.conn_points[3])
                    )
        self.size = (abs(self.conn_points[0] - self.conn_points[2]),
                     abs(self.conn_points[1] - self.conn_points[3])
                     )


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


# sidebar element list (icon_on, icon_off, type, description)
ELEMENT_LIST = (('roadm_on.png', 'roadm_off.png', 'ROADM', 'ROADM element'),
                ('amplifier_on.png', 'amplifier_off.png', 'AMP', 'Amplifier'),
                ('transceiver_on.png', 'transceiver_off.png', 'TRX', 'Transciever'),
                ('fiber_on.png', 'fiber_off.png', 'FIBER', 'Fiber span'),
                ('fused_on.png', 'fused_off.png', 'FUSED', 'Fuse or physical connection'),
                )
FUNCTION_LIST = (('connect_on.png', 'connect_off.png', 'CONNECTION', 'Connection'),
                 ('remove_on.png', 'remove_off.png', 'REMOVE', 'Remove element'),
                )


if __name__ == '__main__':
    Application().run()
