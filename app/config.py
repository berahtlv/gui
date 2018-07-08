'''
Describes application default .ini format and layout of panelview, part of main.py
'''
import os.path

# application location folder
app_path = os.path.dirname(os.path.realpath(__file__))

# default .ini configuration file structure
cfg_defaults = (('DefaultPath', {'theme_path': app_path + r'/themes/default/',
                                'project_path': app_path
                                }
                ),
                ('ColorTheme', {'color': '0.2 0.2 0.2 1'
                                }
                ),
)

# panelview layout
cfg_panels = (('Configuration',
               '''[
                    {"type": "title",
                     "title": "Default path configuration"
                     },
                    {"type": "path",
                     "title": "Theme folder",
                     "desc": "Folder containing application icons",
                     "section": "DefaultPath",
                     "key": "theme_path"
                     },
                    {"type": "path",
                     "title": "Project folder",
                     "desc": "Default project folder",
                     "section": "DefaultPath",
                     "key": "project_path"
                     },
                     {"type": "title",
                      "title": "Window color theme"
                      },
                    {"type": "string",
                     "title": "Window color",
                     "desc": "Color of application window expressed in RGBA format, like '0.2 0.2 0.2 1'",
                     "section": "ColorTheme",
                     "key": "color"
                     }
                    ]'''
                ),
)
