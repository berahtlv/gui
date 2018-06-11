
import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder


'''
Main application Window
'''
class MainWindow(Widget):
    pass


class Sidebar(BoxLayout):
    pass





'''
Application instance with its config
'''
class Application(App):

    # TODO: app configuration

    def build(self):
        mainwindow = Builder.load_file('./kv/main.kv')
        return mainwindow


if __name__ == '__main__':
    Application().run()
