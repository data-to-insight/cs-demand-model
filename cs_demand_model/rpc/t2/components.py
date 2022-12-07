import json
import uuid
from typing import Callable

import plotly
import plotly.graph_objects as go


class Component:
    def __init__(self, id=None, type_name=None):
        if id is None:
            id = uuid.uuid4().hex
        self.id = id

        if type_name is None:
            type_name = type(self).__name__.lower()
        self.type = type_name

    def __json__(self):
        props = [p for p in dir(self) if not p.startswith("_")]
        return {p: getattr(self, p) for p in props}


class Paragraph(Component):
    def __init__(self, text):
        super().__init__(id=id(text))
        self.text = text


class Button(Component):
    def __init__(self, text, action):
        super().__init__()
        self.text = text
        self.action = action


class ButtonBar(Component):
    def __init__(self, *buttons: Button):
        super().__init__()
        self.buttons = buttons


class BoxPage(Component):
    def __init__(self, *components):
        super().__init__()
        self.components = components


class SidebarPage(Component):
    def __init__(self, sidebar: list[Component], main: list[Component]):
        super().__init__()
        self.sidebar = sidebar
        self.main = main


class Chart(Component):
    def __init__(
        self,
        state: "DemandModellingState",
        renderer: Callable[["DemandModellingState"], go.Figure],
    ):
        super().__init__()
        self.__state = state
        self.__renderer = renderer

    @property
    def chart(self):
        chart = self.__renderer(self.__state)
        if isinstance(chart, go.Figure):
            chart = plotly.io.to_json(chart, pretty=True)
        return chart
