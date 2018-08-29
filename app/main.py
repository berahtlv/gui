'''
Network simulator like UI build on Kivy framework
'''
__version__ = '0.0.1'
__author__ = 'Roberts Miculens'
__email__ = 'robertsmg@gmail.com'
__repo__ = 'github.com/berahtlv/gui'
__license__ = 'BSD 3-Clause License'

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
from kivy.uix.gridlayout import GridLayout
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
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             NumericProperty, ReferenceListProperty)
from kivy.core.window import Window
from kivy.factory import Factory

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
                app.root.open_info(title='Info', msg='Change will take effect only after application restart')
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
        app.root = self

    # closes popup window
    def close_popup(self):
        self._popup.dismiss()

    # opens informative popup window with 'OK' button
    def open_info(self, title='About', msg=f'GUI application v{__version__}\n\n'+
                  f'[i][size=11]{__author__}\n{__email__}\n{__repo__}\n{__license__}[/size][/i]'):
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
        if app.root.ids['topomap'].topology:
            #TODO: add test - do topology already saved?
            def _clear_topology():
                # clears topology and graphical representation
                app.root.ids['topomap'].topology.clear()
                app.root.ids['topomap'].clear_widgets()
                # clears TabbedPanel tabs Content
                app.root.ids['paramtab'].content = None
                app.root.ids['topomap']._refresh_paramtab()
                app.root.ids['basictabcontent']._clear_form()
                # closes Popup
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
    menus = (MenuDescr('File', (FuncDescr('New', 'New topology', lambda: app.root.create_new()),
                                FuncDescr('Open', 'Open topology', lambda: app.root.open_open()),
                                FuncDescr('Save', 'Save topology', lambda: app.root.open_save()),
                                FuncDescr('Save As', 'Save As topology', lambda: app.root.open_save()),
                                FuncDescr('Exit', 'Close application', lambda: app.stop())
                                )
                       ),
             MenuDescr('Edit', (FuncDescr('Settings', 'Application settings', lambda: app.open_settings()),
                                )
                       ),
             MenuDescr('View', (FuncDescr('Fullscreen', 'Fullscreen', Window.maximize),
                                )
                       ),
             MenuDescr('Help', (FuncDescr('About', 'About application', lambda: app.root.open_info()),
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
SimMode = namedtuple('SimMode', 'name descr clb')

'''
Main toolbar for Menubar function shortcuts
'''
class Toolbar(BoxLayout):

    # defines Toolbar icons and callback functions of those
    icons = (ToolIconDescr('new_down.png', 'new.png', 'New topology',
                           lambda: app.root.create_new()),
             ToolIconDescr('open_down.png', 'open.png', 'Open topology',
                           lambda: app.root.open_open()),
             ToolIconDescr('save_down.png', 'save.png', 'Save topology',
                           lambda: app.root.open_save()),
             ToolIconDescr('saveas_down.png', 'saveas.png', 'Save As topology',
                           lambda: app.root.open_save()),
             ToolIconDescr('fullscreen_down.png', 'fullscreen.png', 'Fullscreen',
                           Window.maximize),
             ToolIconDescr('settings_down.png', 'settings.png', 'Application settings',
                           lambda: app.open_settings()),
             ToolIconDescr('info_down.png', 'info.png', 'About application',
                           lambda: app.root.open_info()),
    )

    # simulation modes, changes TopomapIcon.ready state
    modes = (SimMode('Advanced', 'Advanced simulation mode - uses only provided configuration',
                     print),
             SimMode('Mixed', 'Mixed simulation mode - mix of auto and advanced simulation modes',
                     print),
             SimMode('Automatic', 'Automatic simulation mode - uses automatically provided configuration',
                     print)
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # toolbar icons added
        for icon in self.icons:
            self.add_widget(ToolbarIcon(icon))

        # padding - empty space
        self.add_widget(Widget(size_hint_x=None, width=50))

        # simulation mode spinner added
        self.add_widget(Label(text='Simulation Mode: ', size_hint_x=None,
                              width=100, font_size=13))
        spinner = Factory.ToolbarSpinner()
        app.simmode = spinner
        spinner.text = '-- select --'
        spinner.values = [spinner.text] + [mode.name for mode in self.modes]
        self.add_widget(spinner)


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

        # sidebar icons added
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
            app.root.ids['topomap'].active_icon = self
        else:
            self.source = self.img
            # drops connectable element list and active icon when unselected
            app.root.ids['topomap'].active_icon = None
            app.root.ids['topomap'].connectable_el = []


# BUG: solve ScrollView bug 'RecursionError: maximum recursion depth exceeded in comparison'
#       sometimes arises when Splitter size is changed
#       Workaround from kivy/kivy Issue #5638 (app not crashes, but topology map floats):
class ScrollViewEdited(ScrollView):
    def _update_effect_bounds(self, *args):
        pass

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
            #       in Windows install, workaround at least for my installation
            connection = TopomapConnect(coord)
            if platform.system() == 'Windows':
                self.add_widget(connection)
            else:
                self.add_widget(connection, canvas='before')
            # updates topology, two edges as conn_dir = 'bidir'
            # gets info about EDFA icon for initialization
            for child in app.root.ids['sidebar'].children[::-1]:
                child_type = getattr(child, 'el_type', 'EMPTY')
                if child_type == 'GEdfa':
                    icon_info = child
                    break
            self.topology.add_edge(*self.connectable_el, obj=connection,
                                   amp_in=GEdfa(icon_info), amp_out=GEdfa(icon_info))
            self.topology.add_edge(*self.connectable_el[::-1], obj=connection,
                                   amp_in=GEdfa(icon_info), amp_out=GEdfa(icon_info))

        # unselects sidebar icon, active_icon and connectable_el are dropped in on_state event
        self.active_icon.state = 'normal'

    def on_selected(self, instance, value):
        # updates BasicTabContent
        app.root.ids['basictab'].content._update(value)

        # changes 'parameters' TabContent
        if isinstance(value, GRoadm):
            param_content = RoadmTabContent()
            app.root.ids['paramtab'].content = param_content
        elif isinstance(value, GFiber):
            param_content = FiberTabContent()
            app.root.ids['paramtab'].content = param_content
        elif isinstance(value, GFused):
            param_content = FusedTabContent()
            app.root.ids['paramtab'].content = param_content
        elif isinstance(value, GEdfa):
            param_content = EdfaTabContent()
            app.root.ids['paramtab'].content = param_content
        elif isinstance(value, GTransceiver):
            param_content = TrxTabContent()
            app.root.ids['paramtab'].content = param_content
        param_content._update(value)

        self._refresh_paramtab()

    # refreshes 'parameters' TabContent
    def _refresh_paramtab(self):
        selected_tab = app.root.ids['tabspanel'].current_tab
        if selected_tab.text == 'Parameters':
            app.root.ids['tabspanel'].switch_to(selected_tab)

    # changes TopomapIcon subclassed elements readiness state
    def _refresh_ready(self, mode):
        if self.children:
            for child in self.children:
                try:
                    # finds elements with .ready attribute
                    getattr(child, 'ready')
                except AttributeError:
                    pass
                else:
                    # changes .ready attribute according to simulation mode
                    if mode == 'Automatic':
                        if not child.ready:
                            child.ready = True
                    elif mode in ('Advanced', 'Mixed', '-- select --'):
                        if child.ready:
                            child.ready = False


'''
Tab content to display basic element info
'''
class BasicTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        for ptinput in (i for i in self.children
                        if isinstance(i, Factory.PTInput) and not i.readonly):
            value = getattr(element, ptinput.param)
            ptinput.text = value if isinstance(value, str) else str(value)

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)

    # clears form values
    def _clear_form(self):
        for ptinput in (i for i in self.children if isinstance(i, Factory.PTInput)):
            ptinput.text = '' if not ptinput.input_filter == 'float' else '0'


'''
Tab content to display Roadm element parameters
'''
class RoadmTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        for child in self.children:
            if isinstance(child, Factory.PTInput) and not child.readonly:
                value = getattr(element, child.param)
                child.text = value if isinstance(value, str) else str(value)
            elif isinstance(child, CheckBox):
                child.active = element.ready
                if app.simmode.text == 'Mixed':
                    child.disabled = False
                else:
                    child.disabled = True

        topology = app.root.ids['topomap'].topology
        edges_in = topology.in_edges(element)
        edges_out = topology.out_edges(element)
        edges = tuple(edges_in) + tuple(edges_out)

        # displays edges info, ensures that childs are added once
        if edges and len(self.children) <= 2:
            label = Factory.PLabel
            input = Factory.PTInput
            spinner = Factory.PSpinner
            titles = (label(text='From Node'), label(text='To Node'),
                      label(text='Amp Out'), label(text='Info'), label(text='Out Gain'), label(text='Out Tilt'),
                      label(text='Amp In'), label(text='Info'), label(text='In Gain'), label(text='In Tilt'))

            self.columns = len(titles)
            self.size_x = self.columns * 175
            self.rows = len(edges) + 2
            self.size_y = self.rows * 29

            # ensures Ready check location, fills GridLayout first column
            for i in range(self.columns - 2):
                self.add_widget(Widget())
            # adds title row
            for title in titles:
                self.add_widget(title)
            # adds parameters rows
            for u, v in edges:
                eparam = topology.get_edge_data(u, v)
                self.add_widget(input(text=u.el_id, readonly=True))
                self.add_widget(input(text=v.el_id, readonly=True))
                self.add_widget(input(text=f"{eparam['amp_out'].type_variety}", readonly=True))
                self.add_widget(Button(text='INFO'))
                self.add_widget(input(text=f"{eparam['amp_out'].gain_target}", readonly=True))
                self.add_widget(input(text=f"{eparam['amp_out'].tilt_target}", readonly=True))
                self.add_widget(input(text=f"{eparam['amp_in'].type_variety}", readonly=True))
                self.add_widget(Button(text='INFO'))
                self.add_widget(input(text=f"{eparam['amp_in'].gain_target}", readonly=True))
                self.add_widget(input(text=f"{eparam['amp_in'].tilt_target}", readonly=True))

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)


'''
Tab content to display Fused element parameters
'''
class FusedTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        for child in self.children:
            if isinstance(child, Factory.PTInput) and not child.readonly:
                value = getattr(element, child.param)
                child.text = value if isinstance(value, str) else str(value)
            elif isinstance(child, CheckBox):
                child.active = element.ready
                if app.simmode.text == 'Mixed':
                    child.disabled = False
                else:
                    child.disabled = True


    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)


'''
Tab content to display Fiber element parameters
'''
class FiberTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        for child in self.children[::-1]:
            if isinstance(child, Factory.PTInput) and not child.readonly:
                value = getattr(element, child.param)
                child.text = value if isinstance(value, str) else str(value)
            elif isinstance(child, Factory.PSpinner) and child.param == 'type_variety':
                value = getattr(element, child.param)
                child.text = value
            elif isinstance(child, CheckBox):
                child.active = element.ready
                if app.simmode.text == 'Mixed':
                    child.disabled = False
                else:
                    child.disabled = True

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)

    # displays equipment values from equipment.json
    def _update_eqpt(self, variety, fiber_disp, fiber_gamma):
        if not variety in ('-- select --'):
            fiber_disp.text = str(self.type_varieties[variety].dispersion)
            fiber_gamma.text = str(self.type_varieties[variety].gamma)
        else:
            fiber_disp.text = ''
            fiber_gamma.text = ''


'''
Tab content to display Edfa element parameters
'''
class EdfaTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        for child in self.children[::-1]:
            if isinstance(child, Factory.PTInput) and not child.readonly:
                value = getattr(element, child.param)
                child.text = value if isinstance(value, str) else str(value)
            elif isinstance(child, Factory.PSpinner) and child.param == 'type_variety':
                value = getattr(element, child.param)
                child.text = value
            elif isinstance(child, CheckBox):
                child.active = element.ready
                if app.simmode.text == 'Mixed':
                    child.disabled = False
                else:
                    child.disabled = True

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)

    # displays equipment values from equipment.json
    def _update_eqpt(self, variety, edfa_gmin, edfa_gmax, edfa_pmax):
        if not variety in ('-- select --'):
            edfa_gmin.text = str(self.type_varieties[variety].gain_min)
            edfa_gmax.text = str(self.type_varieties[variety].gain_flatmax)
            edfa_pmax.text = str(self.type_varieties[variety].p_max)
        else:
            edfa_gmin.text = ''
            edfa_gmax.text = ''
            edfa_pmax.text = ''


'''
Tab content to display Transceiver element parameters
'''
class TrxTabContent(GridLayout):

    # updates form info when element is selected
    def _update(self, element):
        # [::-1] ensures correct update order - 'type_variety' then 'format'
        for child in self.children[::-1]:
            if isinstance(child, Factory.PTInput) and not child.readonly:
                value = getattr(element, child.param)
                child.text = value if isinstance(value, str) else str(value)
            elif isinstance(child, Factory.PSpinner) and child.param in ('type_variety', 'trx_format'):
                value = getattr(element, child.param)
                child.text = value
            elif isinstance(child, CheckBox):
                child.active = element.ready
                if app.simmode.text == 'Mixed':
                    child.disabled = False
                else:
                    child.disabled = True

    # updates element info when form value change occurs
    def _update_el(self, param_name, param_type, readonly, value):
        if not readonly:
            element = app.root.ids['topomap'].selected
            # updates element attributes
            if element and not getattr(element, param_name) == value:
                setattr(element, param_name, value
                        if not param_type == 'float' else float(value) if value else 0)

    # updates format values when type_varieties seleted
    def _update_format(self, value, format_spinner, type_varieties):
        if value != '-- select --':
            format_spinner.text = '-- select --'
            format_spinner.values = ['-- select --'] + [i['format'] for i in type_varieties[value].mode]
        else:
            format_spinner.text = '-- select --'
            format_spinner.values = ['-- select --']

    # displays equipment values from equipment.json
    def _update_eqpt(self, trx_type, trx_variety, trx_baudrate, trx_osnr, trx_bitrate):
        if not trx_variety in ('-- select --'):
            trx_modes = self.type_varieties[trx_type].mode
            trx_mode = [m for m in trx_modes if m['format'] == trx_variety]
            trx_baudrate.text = str(trx_mode[0]['baudrate']/1e9)
            trx_osnr.text = str(trx_mode[0]['OSNR'])
            trx_bitrate.text = str(trx_mode[0]['bit_rate']/1e9)
        else:
            trx_baudrate.text = ''
            trx_osnr.text = ''
            trx_bitrate.text = ''


'''
Displays some mouseover info and application states
'''
class Statusbar(BoxLayout):
    # TODO: add mouseover info and application states
    pass


if __name__ == '__main__':
    Application().run()
