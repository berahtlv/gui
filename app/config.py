'''
Describes application default .ini format and layout of panelview, part of main.py
'''
import os.path

# application location folder
app_path = os.path.dirname(os.path.realpath(__file__))

# default .ini configuration file structure
cfg_defaults = (('DefaultPath', {'theme_path': os.path.join(app_path, 'themes', 'default'),
                                 'json_path': os.path.join(app_path, 'json'),
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
                     "desc": "Contains application interface icons",
                     "section": "DefaultPath",
                     "key": "theme_path"
                     },
                    {"type": "path",
                     "title": "JSON files folder",
                     "desc": "Contains equipment and other configurations in json format",
                     "section": "DefaultPath",
                     "key": "json_path"
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
