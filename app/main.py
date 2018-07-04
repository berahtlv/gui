
import kivy
kivy.require('1.10.0')

# basic app restrictions (SDL2 only!!!)
from kivy.config import Config
Config.set('graphics', 'width', 1024)
Config.set('graphics', 'height', 768)
Config.set('graphics', 'minimum_width', 800)
Config.set('graphics', 'minimum_height', 600)
Config.set('kivy', 'exit_on_escape', 0)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.behaviors.drag import DragBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ObjectProperty, OptionProperty, ListProperty
from kivy.graphics import Color, Line, Rectangle
from kivy.factory import Factory
from kivy.core.window import Window

import networkx as nx
import random
from collections import namedtuple

from popups import InfoPopup, OpenProject, SaveProject, QuestionPopup, QuestionMultiPopup


# TODO:
# 1. App setting panel with default config and its location
# 1.1. main window size restriction
# 1.2. icons theme location (THEMES_FOLDER)
# 1.3. default working directory (PROJECTS_FOLDER)
# 1.4. window colortheme (hardcoded in .kv)

# icons location
THEMES_FOLDER = 'themes/default/'


'''
Application instance with its config
'''
class Application(App):

    def build(self):
        self.title = 'GUI'
        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow


'''
Main application Window
'''
class MainWindow(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # workaround to get all MainWindow ids
        global root
        root = self

    # closes popup window
    def close_popup(self):
        self._popup.dismiss()

    # opens informative popup window with 'OK' button
    def open_info(self, title='Info', msg='Informative message.'):
        content = InfoPopup(_close=self.close_popup, _msg=msg)
        self._popup = Popup(title=title, size_hint=(None,None), size=(250,200),
                            auto_dismiss=False, content=content)
        self._popup.open()

    # opens popup window with two buttons, first button is binded to execute func
    def open_question(self, title='Question', msg='Question message.', btn=['Ok', 'Cancel'], func=None):
        content = QuestionPopup(_close=self.close_popup, _msg=msg, _btn=btn, _func=func)
        self._popup = Popup(title=title, size_hint=(None,None), size=(350,200),
                            auto_dismiss=False, content=content)
        self._popup.open()

    # opens popup window with three buttons, first button is binded to execute func1, second to func2
    def open_question_multi(self, title='Question', msg='Question message.', btn=['Yes', 'No', 'Cancel'],
                            func1=None, func2=None):
        content = QuestionMultiPopup(_close=self.close_popup, _msg=msg, _btn=btn, _func1=func1, _func2=func2)
        self._popup = Popup(title=title, size_hint=(None,None), size=(350,200),
                            auto_dismiss=False, content=content)
        self._popup.open()

    # clears topology for new Project
    def create_new(self):
        if root.ids['topomap'].topology:
            #TODO: add test - do topology already saved?
            def _clear_topology():
                root.ids['topomap'].topology.clear()
                root.ids['topomap'].clear_widgets()
                self._popup.dismiss()
            def _open_save():
                self._popup.dismiss()
                self.open_save()

            self.open_question_multi(msg='Do you want to save changes?\nIf you proceed all changes will be lost!',
                               func1=_open_save, func2=_clear_topology)

    # opens Open Project popup window
    def open_open(self):
        content = OpenProject(_open=self.open_project, _cancel=self.close_popup)
        self._popup = Popup(title='Open Project', size_hint=(None, None), size=(550, 500),
                            auto_dismiss=False, content=content)
        self._popup.open()

    # opens Save/Save As Project popup window
    def open_save(self):
        #TODO: add test - do project already exist and save without popup window
        content = SaveProject(_save=self.save_project, _cancel=self.close_popup)
        self._popup = Popup(title='Save Project', size_hint=(None, None), size=(550, 500),
                            auto_dismiss=False, content=content)
        self._popup.open()

    # opens project from file and adds elements to the topology map
    def open_project(self, filepath):
        #TODO: open topology from file
        self.close_popup()
        print('topology opened:', filepath)

    # saves active topology to the file
    def save_project(self, filepath):
        #TODO: save topology to file
        self.close_popup()
        print('topology saved:', filepath)


MenuDescr = namedtuple('MenuDescr', 'title func')
FuncDescr = namedtuple('FuncDescr', 'name clb')

'''
Main application menubar
'''
class Menubar(BoxLayout):

    menus = (MenuDescr('File', (FuncDescr('New', lambda: root.create_new()),
                                FuncDescr('Open', lambda: root.open_open()),
                                FuncDescr('Save', lambda: root.open_save()),
                                FuncDescr('Save As', lambda: root.open_save()),
                                FuncDescr('Exit', Application().stop)
                                )
                       ),
             MenuDescr('Edit', (FuncDescr('Settings', 'func'),
                                )
                       ),
             MenuDescr('View', (FuncDescr('Fullscreen', Window.maximize),
                                )
                       ),
             MenuDescr('Help', (FuncDescr('About', lambda: root.open_info('About',
                                                                          'GUI application v0.001')),
                                )
                       )
             )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for menu in self.menus:
            self.add_widget(MenubarMenu(menu))


'''
Menubar menu object
'''
class MenubarMenu(Button):

    def __init__(self, menu, **kwargs):
        super().__init__(**kwargs)

        self.text = menu.title
        self.drop = MenuDropDown()
        self.bind(on_release=self.drop.open)

        for func in menu.func:
            l = MenuButton(self, func.clb, text=func.name)
            self.drop.add_widget(l)


'''
Menu DropDown object
'''
class MenuDropDown(DropDown):

    def on_select(self, clb):
        #TODO: remove if statement when all icons will be implemented
        if not clb == 'func':
            clb()
        else:
            print(clb)


'''
Menu button object
'''
class MenuButton(Button):

    def __init__(self, main_btn, clb, **kwargs):
        super().__init__(**kwargs)

        self.bind(on_release=lambda btn: main_btn.drop.select(clb))


ToolIconDescr = namedtuple('ToolIconDescr', 'down normal type descr clb')

'''
Main toolbar for Menubar function shortcuts
'''
class Toolbar(BoxLayout):

    icons = (ToolIconDescr('new_down.png', 'new.png' , 'NEW', 'New topology', lambda: root.create_new()),
             ToolIconDescr('open_down.png', 'open.png' , 'OPEN', 'Open topology', lambda: root.open_open()),
             ToolIconDescr('save_down.png', 'save.png', 'SAVE', 'Save topology', lambda: root.open_save()),
             ToolIconDescr('saveas_down.png', 'saveas.png', 'SAVE AS', 'Save As topology', lambda: root.open_save()),
             ToolIconDescr('fullscreen_down.png', 'fullscreen.png', 'FULLSCREEN', 'Fullscreen', Window.maximize),
             ToolIconDescr('settings_down.png', 'settings.png', 'SETTINGS', 'Application settings', 'func'),
             ToolIconDescr('info_down.png', 'info.png', 'INFO', 'About application', lambda: root.open_info('About',
                                                                                                        'GUI application v0.001')),
             )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for icon in self.icons:
            self.add_widget(ToolbarIcon(icon))


'''
Main toolbar icon object
'''
class ToolbarIcon(ButtonBehavior, Image):

    def __init__(self, icon_info, **kwargs):
        super().__init__(**kwargs)
        self.img_down, self.img, self.type, self.descr, self.clb = icon_info
        self.source = THEMES_FOLDER + self.img
        #TODO: remove if statement when all icons will be implemented
        if not self.clb == 'func':
            self.bind(on_release=lambda btn: self.clb())

    def on_state(self, widget, value):
        if value == 'down':
            self.source = THEMES_FOLDER + self.img_down
        else:
            self.source = THEMES_FOLDER + self.img


SideIconDescr = namedtuple('SideIconDescr', 'down normal type descr')

'''
Sidebar with element list
'''
class Sidebar(BoxLayout):

    icons_el = (SideIconDescr('roadm_down.png', 'roadm.png', 'ROADM', 'ROADM element'),
               SideIconDescr('amplifier_down.png', 'amplifier.png', 'EDFA', 'Amplifier'),
               SideIconDescr('transceiver_down.png', 'transceiver.png', 'TRX', 'Transciever'),
               SideIconDescr('fiber_down.png', 'fiber.png', 'FIBER', 'Fiber span'),
               SideIconDescr('fused_down.png', 'fused.png', 'FUSED', 'Fuse or physical connection'),
               )
    icons_func = (SideIconDescr('connect_down.png', 'connect.png', 'CONNECTION', 'Connection'),
                 SideIconDescr('remove_down.png', 'remove.png', 'REMOVE', 'Remove element'),
                )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_widget(Widget())
        for icon in self.icons_el:
            self.add_widget(SidebarIcon(icon))
        self.add_widget(Widget(size_hint=(1, None), height=50))
        for icon in self.icons_func:
            self.add_widget(SidebarIcon(icon))
        self.add_widget(Widget())


'''
Sidebar element object
'''
class SidebarIcon(ToggleButtonBehavior, Image):

    def __init__(self, icon_info, **kwargs):
        super().__init__(**kwargs)
        self.img_down, self.img, self.el_type, self.el_descr = icon_info
        self.source = THEMES_FOLDER + self.img

    def on_state(self, widget, value):
        if value == 'down':
            self.source = THEMES_FOLDER + self.img_down
            root.ids['topomap'].active_icon = self
        else:
            self.source = THEMES_FOLDER + self.img
            # drops connectable element list and active icon when unselected
            root.ids['topomap'].active_icon = None
            root.ids['topomap'].connectable_el = []


'''
Topology map with draggable elements
'''
class TopologyMap(RelativeLayout):

    active_icon = ObjectProperty(None, allownone=True)
    connectable_el = ListProperty([])
    topology = ObjectProperty(nx.Graph()) #TODO: change to DiGraph

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

    def __init__(self, active_obj, **kwargs):
        super().__init__(**kwargs)
        self.img = active_obj.img
        self.img_down = active_obj.img_down
        self.el_type = active_obj.el_type
        self.source = THEMES_FOLDER + self.img
        self.el_id = 'ID'+''.join((str(random.randrange(0,9)) for i in range(3)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.source = THEMES_FOLDER + self.img_down

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
        if not self.source == THEMES_FOLDER + self.img:
            self.source = THEMES_FOLDER + self.img

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


if __name__ == '__main__':
    Application().run()
