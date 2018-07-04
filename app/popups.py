'''
Describes content of Popups, addition to main.py
'''
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty

'''
Info popup content
'''
class InfoPopup(BoxLayout):

    _msg = StringProperty('')
    _close = ObjectProperty(None)


'''
Question popup content
'''
class QuestionPopup(BoxLayout):

    _msg = StringProperty('')
    _close = ObjectProperty(None)
    _func = ObjectProperty(None)
    _btn = ListProperty([])


'''
Content of Question popup with two answers
'''
class QuestionMultiPopup(BoxLayout):

    _msg = StringProperty('')
    _close = ObjectProperty(None)
    _func1 = ObjectProperty(None)
    _func2 = ObjectProperty(None)
    _btn = ListProperty([])


'''
Open Project popup content
'''
class OpenProject(BoxLayout):

    _open = ObjectProperty(None)
    _cancel = ObjectProperty(None)


'''
Save Project popup content
'''
class SaveProject(BoxLayout):

    _save = ObjectProperty(None)
    _cancel = ObjectProperty(None)
