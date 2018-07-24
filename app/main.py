'''
Network simulator like UI build on Kivy framework
'''
__version__ = '0.0.1'
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
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             NumericProperty, ReferenceListProperty)
from kivy.core.window import Window

import networkx as nx
import platform, os.path
from collections import namedtuple

from popups import InfoPopup, OpenProject, SaveProject, QuestionPopup, QuestionMultiPopup
from config import cfg_defaults, cfg_panels
from elements import TopomapConnect, GRoadm, GEdfa, GTransceiver, GFiber, GFused


'''
Application instance with its config
'''
class Application(App):

    theme_path = StringProperty()
    json_path = StringProperty()
    project_path = StringProperty()
    colortheme = ListProperty()

    def build(self):
        global app
        app = self

        self.theme_path = os.path.join(self.config.get('DefaultPath', 'theme_path'), '')
        self.json_path = os.path.join(self.config.get('DefaultPath', 'json_path'), '')
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
                self.theme_path = os.path.join(value, '')
                root.open_info(title='Info', msg='Change will take effect only after application restart')
            elif pair == ('DefaultPath', 'json_path'):
                self.json_path = os.path.join(value, '')
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
FuncDescr = namedtuple('FuncDescr', 'name descr clb')

'''
Main application menubar
'''
class Menubar(BoxLayout):

    # defines Menubar menu headers and menu items with callback functions
    menus = (MenuDescr('File', (FuncDescr('New', 'New topology', lambda: root.create_new()),
                                FuncDescr('Open', 'Open topology', lambda: root.open_open()),
                                FuncDescr('Save', 'Save topology', lambda: root.open_save()),
                                FuncDescr('Save As', 'Save As topology', lambda: root.open_save()),
                                FuncDescr('Exit', 'Close application', lambda: app.stop())
                                )
                       ),
             MenuDescr('Edit', (FuncDescr('Settings', 'Application settings', lambda: app.open_settings()),
                                )
                       ),
             MenuDescr('View', (FuncDescr('Fullscreen', 'Fullscreen', Window.maximize),
                                )
                       ),
             MenuDescr('Help', (FuncDescr('About', 'About application', lambda: root.open_info()),
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


ToolIconDescr = namedtuple('ToolIconDescr', 'down normal descr clb')

'''
Main toolbar for Menubar function shortcuts
'''
class Toolbar(BoxLayout):

    # defines Toolbar icons and callback functions of those
    icons = (ToolIconDescr('new_down.png', 'new.png', 'New topology',
                           lambda: root.create_new()),
             ToolIconDescr('open_down.png', 'open.png', 'Open topology',
                           lambda: root.open_open()),
             ToolIconDescr('save_down.png', 'save.png', 'Save topology',
                           lambda: root.open_save()),
             ToolIconDescr('saveas_down.png', 'saveas.png', 'Save As topology',
                           lambda: root.open_save()),
             ToolIconDescr('fullscreen_down.png', 'fullscreen.png', 'Fullscreen',
                           Window.maximize),
             ToolIconDescr('settings_down.png', 'settings.png', 'Application settings',
                           lambda: app.open_settings()),
             ToolIconDescr('info_down.png', 'info.png', 'About application',
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
        self.img_down = app.theme_path + icon_info.down
        self.img = app.theme_path + icon_info.normal
        self.descr = icon_info.descr
        self.clb = icon_info.clb
        self.source = self.img
        self.bind(on_release=lambda btn: self.clb())

    def on_state(self, instance, value):
        if value == 'down':
            self.source = self.img_down
        else:
            self.source = self.img


SideIconDescr = namedtuple('SideIconDescr', 'down normal type descr')

'''
Sidebar with element list
'''
class Sidebar(BoxLayout):

    # defines Sidebar Element icons and types of those
    icons_el = (SideIconDescr('roadm_down.png', 'roadm.png', 'GRoadm', 'ROADM element'),
               SideIconDescr('amplifier_down.png', 'amplifier.png', 'GEdfa', 'Amplifier'),
               SideIconDescr('transceiver_down.png', 'transceiver.png', 'GTransceiver', 'Transceiver'),
               SideIconDescr('fiber_down.png', 'fiber.png', 'GFiber', 'Fiber span'),
               SideIconDescr('fused_down.png', 'fused.png', 'GFused', 'Fuse or physical connection'),
    )
    # defines Sidebar Function icons and types of those
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
        self.img_down = app.theme_path + icon_info.down
        self.img = app.theme_path + icon_info.normal
        self.el_type = icon_info.type
        self.el_descr = icon_info.descr
        self.source = self.img

    def on_state(self, instance, value):
        if value == 'down':
            self.source = self.img_down
            root.ids['topomap'].active_icon = self
        else:
            self.source = self.img
            # drops connectable element list and active icon when unselected
            root.ids['topomap'].active_icon = None
            root.ids['topomap'].connectable_el = []


'''
Topology map with draggable elements
'''
class TopologyMap(RelativeLayout):

    active_icon = ObjectProperty(None, allownone=True) # active sidebar icon
    connectable_el = ListProperty() # list to store elements for connection
    topology = ObjectProperty(nx.DiGraph()) # graphical representation topology
    selected = ObjectProperty() # topology map selected element, for params

    def on_touch_down(self, touch):
        if self.active_icon and self.collide_point(*touch.pos):
            if not self.active_icon.el_type in ['REMOVE', 'CONNECTION']:
                cls = globals()[self.active_icon.el_type]
                new_element = cls(self.active_icon,
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

    def on_selected(self, instance, value):
        # updates BasicTabContent
        root.ids['basictab'].content._update(value)

        # changes 'parameters' TabContent
        if isinstance(value, GRoadm):
            root.ids['paramtab'].content = RoadmTabContent()
        elif isinstance(value, GFiber):
            root.ids['paramtab'].content = FiberTabContent()

        # refreshes 'parameters' TabContent
        selected_tab = root.ids['tabspanel'].current_tab
        if selected_tab.text == 'Parameters':
            root.ids['tabspanel'].switch_to(selected_tab)


'''
Tab content to display basic element info
'''
class BasicTabContent(BoxLayout):

    # TODO: clear form values after Element deletion or New topology selection

    # updates form info when element is selected
    def _update(self, element):
        for paramlabel in self.children:
            value = getattr(element, paramlabel.lparam)
            paramlabel.lvalue = value if isinstance(value, str) else str(value)

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, value):
        element = root.ids['topomap'].selected
        # updates element attributes
        if element:
            setattr(element, param_name, value if not param_type == 'float' else float(value))

        # updates form info
        for paramlabel in self.children:
            if paramlabel.lparam == param_name:
                paramlabel.lvalue = value
                break


'''
Tab content to display Roadm element parameters
'''
class RoadmTabContent(BoxLayout):

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, value):
        pass


'''
Tab content to display Fiber element parameters
'''
class FiberTabContent(BoxLayout):

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, value):
        pass


'''
Displays some mouseover info and application states
'''
class Statusbar(BoxLayout):
    # TODO: add mouseover info and application states
    pass


if __name__ == '__main__':
    Application().run()
