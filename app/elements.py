'''
Describes topology map element objects, part of main.py
'''
from kivy.app import App
from kivy.uix.behaviors.drag import DragBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import (StringProperty, NumericProperty, ListProperty,
                             OptionProperty, ReferenceListProperty,
                             BooleanProperty)

import random
from collections import namedtuple

'''
Draggable element Baseclass
'''
class TopomapIcon(DragBehavior, Image):

    el_type = StringProperty()
    el_side = NumericProperty(50) # size of square side, code assumes squared icon

    ready = BooleanProperty(False)

    el_id = StringProperty()
    el_site = StringProperty()
    el_region = StringProperty()
    el_latitude = NumericProperty()
    el_longitude = NumericProperty()

    def __init__(self, active_obj, **kwargs):
        super().__init__(**kwargs)
        self.img = active_obj.img
        self.img_down = active_obj.img_down
        self.el_type = active_obj.el_type
        self.source = self.img
        # default values
        self.el_id = 'ID' + ''.join((str(random.randrange(0,9)) for i in range(3)))
        self.el_latitude = round(self.y, 2)
        self.el_longitude = round(self.x, 2)
        # 'automatic' simulation mode
        if App.get_running_app().simmode.text == 'Automatic':
            self.ready = True

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.source = self.img_down

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

                # clears TabbedPanel tabs Content
                app = App.get_running_app()
                if app.root.ids['topomap'].selected is self:
                    app.root.ids['paramtab'].content = None
                    app.root.ids['topomap']._refresh_paramtab()
                    app.root.ids['basictabcontent']._clear_form()

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

            # updates selected element TopologyMap property for ParamTabs use
            self.parent.selected = self

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        # w/o collision, mouse can be released outside of collision region
        if not self.source == self.img:
            self.source = self.img

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

    def on_ready(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered
    def _ensure_ready(self, simmode):
        raise NotImplementedError('Implementation left for derivative classes')


'''
ROADM draggable element
'''
class GRoadm(TopomapIcon):

    loss = NumericProperty(17)
    params = ReferenceListProperty(loss)

    def on_params(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered
    def _ensure_ready(self, simmode):
        # any attenuation value allowed
        self.ready = True
        # updates 'Parameters' tab
        app = App.get_running_app()
        if app.root.ids['topomap'].selected is self:
            app.root.ids['paramtab'].content.items[0].active = self.ready


'''
EDFA draggable element
'''
class GEdfa(TopomapIcon):

    gain_target = NumericProperty()
    tilt_target = NumericProperty(0)
    type_variety = StringProperty('-- select --')
    params = ReferenceListProperty(gain_target, tilt_target, type_variety)

    def on_params(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered correctly
    def _ensure_ready(self, simmode):
        app = App.get_running_app()
        if simmode == 'Automatic' and self.type_variety != '-- select --':
            self.ready = True
        elif simmode in ('Advanced', 'Mixed') and self.type_variety != '-- select --':
            amp = app.root.ids['paramtab'].equipment['Edfa'][self.type_variety]
            if amp.gain_flatmax >= self.gain_target >= amp.gain_min:
                self.ready = True
            else:
                self.ready = False
        else:
            self.ready = False

        # updates 'Parameters' tab
        if app.root.ids['topomap'].selected is self:
            app.root.ids['paramtab'].content.items[0].active = self.ready


'''
Transceiver draggable element
'''
class GTransceiver(TopomapIcon):

    type_variety = StringProperty('-- select --')
    trx_format = StringProperty('-- select --')
    params = ReferenceListProperty(type_variety, trx_format)

    def on_params(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered
    def _ensure_ready(self, simmode):
        if self.type_variety != '-- select --' and self.trx_format != '-- select --':
            self.ready = True
        else:
            self.ready = False

        # updates 'Parameters' tab
        app = App.get_running_app()
        if app.root.ids['topomap'].selected is self:
            app.root.ids['paramtab'].content.items[0].active = self.ready


'''
Fused draggable element
'''
class GFused(TopomapIcon):

    loss = NumericProperty(0.5)
    params = ReferenceListProperty(loss)

    def on_params(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered
    def _ensure_ready(self, simmode):
        # any attenuation value allowed
        self.ready = True
        # updates 'Parameters' tab
        app = App.get_running_app()
        if app.root.ids['topomap'].selected is self:
            app.root.ids['paramtab'].content.items[0].active = self.ready


'''
Fiber draggable element
'''
class GFiber(TopomapIcon):

    length = NumericProperty()
    loss_coef = NumericProperty(0.2)
    type_variety = StringProperty('-- select --')
    params = ReferenceListProperty(length, loss_coef, type_variety)

    def on_params(self, instance, value):
        self._ensure_ready(App.get_running_app().simmode.text)

    # verifies that all required parameters are entered
    def _ensure_ready(self, simmode):
        if self.length > 0:
            self.ready = True
        else:
            self.ready = False

        # updates 'Parameters' tab
        app = App.get_running_app()
        if app.root.ids['topomap'].selected is self:
            app.root.ids['paramtab'].content.items[0].active = self.ready


'''
Draggable elements connection
'''
class TopomapConnect(Widget):

    conn_dir = OptionProperty('bidir', options=['bidir', 'unidir'])
    conn_color = ListProperty()
    conn_points = ListProperty()

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

                return True if (len_AC * sinA) <= distance else False

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

    def on_conn_dir(self, instance, value):
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
