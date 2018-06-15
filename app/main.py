
import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout


'''
Main application Window
'''
class MainWindow(BoxLayout):
    pass

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
Sidebar with drag and drop element list
'''
class Sidebar(BoxLayout):
    pass

'''
Sidebar element
'''
class SidebarIcon(Button):
    pass

'''
Topology map with draggable elements
'''
class TopologyMap(FloatLayout):
    pass

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
    # 1.2. icons theme location
    # 1.3. default working directory

    def build(self):
        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow


if __name__ == '__main__':
    Application().run()
