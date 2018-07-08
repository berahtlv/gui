'''
Network simulator like UI build on Kivy framework.
'''
__version__ = '0.001'
__author__ = 'Roberts Miculens'
__email__ = 'robertsmg@gmail.com'
__repo__ = 'github.com/berahtlv/gui'

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
from kivy.uix.settings import SettingsWithSidebar
from kivy.properties import (StringProperty, ObjectProperty, OptionProperty,
                             ListProperty, NumericProperty)
from kivy.core.window import Window

import networkx as nx
import random, os.path, platform
from collections import namedtuple

from popups import InfoPopup, OpenProject, SaveProject, QuestionPopup, QuestionMultiPopup
from config import cfg_defaults, cfg_panels

'''
Application instance with its config
'''
class Application(App):

    theme_path = StringProperty('')
    project_path = StringProperty('')
    colortheme = ListProperty('')

    def build(self):
        global app
        app = self

        self.theme_path = self.config.get('DefaultPath', 'theme_path')
        self.project_path = self.config.get('DefaultPath', 'project_path')
        colortheme = [float(i) for i in self.config.get('ColorTheme', 'color').split()]
        self.colortheme = colortheme if len(colortheme) == 4 else [0.2, 0.2, 0.2, 1] # ensures correct color format
        self.title = 'GUI'
        self.use_kivy_settings = False # disables Kivy configuration section
        self.settings_cls = SettingsWithSidebar # Kivy panel style

        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow

    def build_config(self, config):
        # sets .ini file format
        for cfg in cfg_defaults:
            config.setdefaults(*cfg)

    def build_settings(self, settings):
        # sets panelview layout
        for title, paneldata in cfg_panels:
            settings.add_json_panel(title, self.config, data=paneldata)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            pair = (section, key)
            if pair == ('DefaultPath', 'theme_path'):
                self.theme_path = value + '/'
                root.open_info(title='Info', msg='Change will take effect only after application restart')
            elif pair == ('DefaultPath', 'project_path'):
                self.project_path = value
            elif pair == ('ColorTheme', 'color'):
                colortheme = [float(i) for i in value.split()]
                self.colortheme = colortheme if len(colortheme) == 4 else [0.2, 0.2, 0.2, 1]


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
    def open_info(self, title='About', msg=f'GUI application v{__version__}\n\n'+
                  f'[i][size=11]{__author__}\n{__email__}\n{__repo__}[/size][/i]'):
        content = InfoPopup(_close=self.close_popup, _msg=msg)
        self._popup = Popup(title=title, size_hint=(None,None), size=(350,200),
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
                                FuncDescr('Exit', lambda: app.stop())
                                )
                       ),
             MenuDescr('Edit', (FuncDescr('Settings', lambda: app.open_settings()),
                                )
                       ),
             MenuDescr('View', (FuncDescr('Fullscreen', Window.maximize),
                                )
                       ),
             MenuDescr('Help', (FuncDescr('About', lambda: root.open_info()),
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
            clb()


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

    icons = (ToolIconDescr('new_down.png', 'new.png' , 'NEW', 'New topology',
                           lambda: root.create_new()),
             ToolIconDescr('open_down.png', 'open.png' , 'OPEN', 'Open topology',
                           lambda: root.open_open()),
             ToolIconDescr('save_down.png', 'save.png', 'SAVE', 'Save topology',
                           lambda: root.open_save()),
             ToolIconDescr('saveas_down.png', 'saveas.png', 'SAVE AS', 'Save As topology',
                           lambda: root.open_save()),
             ToolIconDescr('fullscreen_down.png', 'fullscreen.png', 'FULLSCREEN', 'Fullscreen',
                           Window.maximize),
             ToolIconDescr('settings_down.png', 'settings.png', 'SETTINGS', 'Application settings',
                           lambda: app.open_settings()),
             ToolIconDescr('info_down.png', 'info.png', 'INFO', 'About application',
                           lambda: root.open_info()),
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
        self.source = app.theme_path + self.img
        self.bind(on_release=lambda btn: self.clb())

    def on_state(self, widget, value):
        if value == 'down':
            self.source = app.theme_path + self.img_down
        else:
            self.source = app.theme_path + self.img


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
        self.source = app.theme_path + self.img

    def on_state(self, widget, value):
        if value == 'down':
            self.source = app.theme_path + self.img_down
            root.ids['topomap'].active_icon = self
        else:
            self.source = app.theme_path + self.img
            # drops connectable element list and active icon when unselected
            root.ids['topomap'].active_icon = None
            root.ids['topomap'].connectable_el = []


'''
Topology map with draggable elements
'''
class TopologyMap(RelativeLayout):

    active_icon = ObjectProperty(None, allownone=True)
    connectable_el = ListProperty([])
    topology = ObjectProperty(nx.DiGraph())

    def on_touch_down(self, touch):
        if self.active_icon and self.collide_point(*touch.pos):
            if not self.active_icon.el_type in ['REMOVE', 'CONNECTION']:
                #TODO: add subclassed TopomapIcon elements
                new_element = TopomapIcon(self.active_icon,
                                          pos=self.to_local(*(i - 25 for i in touch.pos))
                                          )
                self.topology.add_node(new_element)
                self.add_widget(new_element)

                return True

        return super().on_touch_down(touch)

    # connects topomap icons based on accumulated connectable_el objects
    def _connect_el(self):
        # checks if connection between nodes already exist, excludes parallel edges
        # TopomapConnect.conn_dir controls direction type and related edges
        # conn_dir = 'bidir' by default
        if not (self.topology.has_edge(*self.connectable_el) or
                self.topology.has_edge(*self.connectable_el[::-1])
                ):
            coord = TopomapConnect.get_coord(*self.connectable_el)

            # adds graphical representation
            # TODO: find the reason of unexpected keyword argument 'canvas'
            #       workaround at least for my installation
            connection = TopomapConnect(coord)
            if platform.system() == 'Windows':
                self.add_widget(connection)
            else:
                self.add_widget(connection, canvas='before')
            # updates topology, two edges as conn_dir = 'bidir'
            self.topology.add_edge(*self.connectable_el, obj=connection)
            self.topology.add_edge(*self.connectable_el[::-1], obj=connection)

        # unselects sidebar icon, active_icon and connectable_el are dropped in on_state event
        self.active_icon.state = 'normal'


'''
Draggable element
'''
class TopomapIcon(DragBehavior, Image):

    el_type = StringProperty('')
    el_id = StringProperty('')
    el_side = NumericProperty(50) # size of square side, code assumes squared icon

    def __init__(self, active_obj, **kwargs):
        super().__init__(**kwargs)
        self.img = active_obj.img
        self.img_down = active_obj.img_down
        self.el_type = active_obj.el_type
        self.source = app.theme_path + self.img
        self.el_id = 'ID'+''.join((str(random.randrange(0,9)) for i in range(3)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.source = app.theme_path + self.img_down

            # removes element and all its connections from map and topology graph
            if getattr(self.parent.active_icon, 'el_type', None) == 'REMOVE':
                # removes related TopomapConnect objects from TopologyMap
                if self.parent.topology.in_edges(self) or self.parent.topology.out_edges(self):
                    edges = tuple(self.parent.topology.in_edges(self, data=True)) + \
                                tuple(self.parent.topology.out_edges(self, data=True))
                    for u, v, c in edges:
                        uniq = []
                        if c not in uniq:
                            # ensures that connection is removed once
                            uniq.append(c)
                            self.parent.remove_widget(c['obj'])

                # related DiGraph edges are removed automatically
                self.parent.topology.remove_node(self)
                self.parent.remove_widget(self)

                return True

            # create connection between topomap icons
            if getattr(self.parent.active_icon, 'el_type', None) == 'CONNECTION':
                # excludes self loops
                if not self in self.parent.connectable_el:
                    self.parent.connectable_el.append(self)

                if len(self.parent.connectable_el) == 2:
                    self.parent._connect_el()

                return True

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        # w/o collision, mouse can be released outside of collision region
        if not self.source == app.theme_path + self.img:
            self.source = app.theme_path + self.img

        return super().on_touch_up(touch)

    def on_pos(self, instance, value):
        if self.parent:
            # updates connection lines
            if self.parent.topology.in_edges(self) or self.parent.topology.out_edges(self):
                edges = tuple(self.parent.topology.in_edges(self, data=True)) + \
                            tuple(self.parent.topology.out_edges(self, data=True))
                for u, v, c in edges:
                    uniq = []
                    if c not in uniq:
                        # ensures that connection is moved once
                        uniq.append(c)
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

        self.size = (max(abs(coord[0] - coord[2]), 4),
                     max(abs(coord[1] - coord[3]), 4)
                     )
        self.pos = (min(coord[0], coord[2]),
                    min(coord[1], coord[3])
                    )
        self.conn_color = [0, 0.6, 0, 1]
        self.conn_points = coord

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # returns True if touch position is closer than distance value
            # assumes: A and B are poins of connection Line, C is touch point
            def _very_close(A, B, C=touch.pos, distance=2):
                Vector = namedtuple('Vector', 'x y')
                vec_AB = Vector(B[0] - A[0], B[1] - A[1])
                vec_AC = Vector(C[0] - A[0], C[1] - A[1])
                len_AB = pow(vec_AB.x**2 + vec_AB.y**2, 1/2)
                len_AC = pow(vec_AC.x**2 + vec_AC.y**2, 1/2)
                mult = vec_AB.x * vec_AC.x + vec_AB.y * vec_AC.y
                cosA = mult / (len_AB * len_AC)
                sinA = pow(1-cosA**2, 1/2)

                return True if (len_AC * sinA) < distance else False

            pos_A = self.conn_points[:2]
            pos_B = self.conn_points[-2:]
            # checks for collision in smaller region
            if _very_close(pos_A, pos_B):
                self.conn_color = [1, 0, 0, 1]

                # removes connections from map and topology graph
                if getattr(self.parent.active_icon, 'el_type', None) == 'REMOVE':
                    # removes all DiGraph edges with associated TopomapConnect object
                    edges = [(u, v)
                             for u, v, c in self.parent.topology.edges(data=True)
                             if c['obj'] is self]
                    for edge in edges:
                        self.parent.topology.remove_edge(*edge)
                    # removes TopomapConnect object from TopologyMap
                    self.parent.remove_widget(self)

                return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if not self.conn_color == [0, 0.6, 0, 1]:
            self.conn_color = [0, 0.6, 0, 1]
        return super().on_touch_up(touch)

    def on_conn_dir(self, inst, value):
        if value == 'bidir':
            # adds opposite direction, as connection was unidirectional
            # assumes one node pair - edge
            edge = [(u, v)
                     for u, v, c in self.parent.topology.edges(data=True)
                     if c['obj'] is self]
            assert len(edge) == 1, f'For some reason "unidir" connection has {len(edge)} edges'
            self.parent.topology.add_edge(*edge[0][::-1], obj=self)

        elif value == 'unidir':
            # removes opposite direction, as connection was bidirectional
            # assumes two node pairs - edges
            edges = [(u, v)
                     for u, v, c in self.parent.topology.edges(data=True)
                     if c['obj'] is self]
            assert len(edges) == 2, f'For some reason "bidir" connection has {len(edges)} edges'
            self.parent.topology.remove_edge(*edges[1])

    # changes direction value
    def _change_dir(self):
        self.conn_dir = 'bidir' if self.conn_dir == 'unidir' else 'unidir'

    # swaps connection source, used for unidirectional connection
    def _change_dir_src(self):
        if self.conn_dir == 'unidir':
            # assumes one node pair - edge
            edge = [(u, v)
                     for u, v, c in self.parent.topology.edges(data=True)
                     if c['obj'] is self]
            assert len(edge) == 1, f'For some reason "unidir" connection has {len(edge)} edges'
            self.parent.topology.add_edge(*edge[0][::-1], obj=self)
            self.parent.topology.remove_edge(*edge[0])

    # updates connection position after TopomapIcon movement
    def _update(self, A, B):
        self.conn_points = self.get_coord(A, B)
        self.pos = (min(self.conn_points[0], self.conn_points[2]),
                    min(self.conn_points[1], self.conn_points[3])
                    )
        self.size = (max(abs(self.conn_points[0] - self.conn_points[2]), 4),
                     max(abs(self.conn_points[1] - self.conn_points[3]), 4)
                     )

    # calculates and returns connection Line coordinates based on two involved TopomapIcon objects
    @staticmethod
    def get_coord(A, B):
        if isinstance(A, TopomapIcon) and isinstance(B, TopomapIcon):
            LinePoint = namedtuple('LinePoint', 'x y')
            # based on calculation from/to center of the icon
            dx = dy = A.el_side / 2
            pos_A = LinePoint(A.x + dx, A.y + dy)
            pos_B = LinePoint(B.x + dx, B.y + dy)

            # if Line is parallel to Y axis
            if pos_A.x == pos_B.x:
                # A below B
                if pos_A.y < pos_A.y + dy <= pos_B.y:
                    pos_A = pos_A._replace(y=pos_A.y + dy)
                    pos_B = pos_B._replace(y=pos_B.y - dy)

                # A above B
                elif pos_A.y > pos_A.y - dy >= pos_B.y:
                    pos_A = pos_A._replace(y=pos_A.y - dy)
                    pos_B = pos_B._replace(y=pos_B.y + dy)

                return pos_A + pos_B

            # if Line is parallel to X axis
            elif pos_A.y == pos_B.y:
                # B from right side of A
                if pos_A.x < pos_A.x + dx <= pos_B.x:
                    pos_A = pos_A._replace(x=pos_A.x + dx)
                    pos_B = pos_B._replace(x=pos_B.x - dx)

                # B from left side of A
                elif pos_B.x <= pos_A.x - dx < pos_A.x:
                    pos_A = pos_A._replace(x=pos_A.x - dx)
                    pos_B = pos_B._replace(x=pos_B.x + dx)

                return pos_A + pos_B

            # Line not parallel to X or Y axis (using y = ax + c)
            else:
                a = (pos_A.y - pos_B.y) / (pos_A.x - pos_B.x)
                c = pos_A.y - a * pos_A.x

                # finding the direction of the line based on slope coefficient
                if (1 >= a > 0) or (0 > a >= -1):
                    # B is from left side
                    if pos_A.x < pos_A.x + dx <= pos_B.x:
                        y = a * (pos_A.x + dx) + c
                        pos_A = pos_A._replace(x=pos_A.x + dx, y=y)
                        y = a * (pos_B.x - dx) + c
                        pos_B = pos_B._replace(x=pos_B.x - dx, y=y)

                    # B is from right side
                    elif pos_B.x <= pos_A.x - dx < pos_A.x:
                        y = a * (pos_A.x - dx) + c
                        pos_A = pos_A._replace(x=pos_A.x - dx, y=y)
                        y = a * (pos_B.x + dx) + c
                        pos_B = pos_B._replace(x=pos_B.x + dx, y=y)

                    return pos_A + pos_B

                elif a > 1 or a < -1:
                    # B is above
                    if pos_A.y < pos_A.y + dy <= pos_B.y:
                        x = (pos_A.y + dy - c) / a
                        pos_A = pos_A._replace(x=x, y=pos_A.y + dy)
                        x = (pos_B.y - dy - c) / a
                        pos_B = pos_B._replace(x=x, y=pos_B.y - dy)

                    # B is below
                    elif pos_A.y > pos_A.y - dy >= pos_B.y:
                        x = (pos_A.y - dy - c) / a
                        pos_A = pos_A._replace(x=x, y=pos_A.y - dy)
                        x = (pos_B.y + dy - c) / a
                        pos_B = pos_B._replace(x=x, y=pos_B.y + dy)

                    return pos_A + pos_B


'''
Displays some mouseover info and application states
'''
class Statusbar(BoxLayout):
    # TODO: add status events
    pass


if __name__ == '__main__':
    Application().run()
