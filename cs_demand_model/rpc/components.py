import hashlib
import logging
import uuid
from typing import Callable, Dict, List, Literal, Optional

import plotly
import plotly.graph_objects as go

from cs_demand_model.rpc.figs import placeholder

logger = logging.getLogger(__name__)


class Component:
    def __init__(self, id=None, type_name=None):
        if id is None:
            id = uuid.uuid4().hex
        try:
            self.id = id
        except AttributeError:
            # If we override the ID property in the component
            pass

        if type_name is None:
            type_name = type(self).__name__.lower()
        self.type = type_name

    def __json__(self):
        props = [p for p in dir(self) if not p.startswith("_")]
        return {p: getattr(self, p) for p in props}


class Paragraph(Component):
    def __init__(self, text, strong=False):
        super().__init__(id=id(text))
        self.text = text
        self.strong = strong


class Button(Component):
    def __init__(
        self,
        text,
        action,
        disabled=False,
        variant: Literal["text", "contained", "outlined"] = "contained",
        start_icon: str = None,
        end_icon: str = None,
    ):
        super().__init__()
        self.text = text
        self.action = action
        self.disabled = disabled
        self.variant = variant
        self.start_icon = start_icon
        self.end_icon = end_icon


class ButtonBar(Component):
    def __init__(self, *buttons: Button):
        super().__init__()
        self.buttons = buttons


class BoxPage(Component):
    def __init__(self, *components, id: str = None):
        super().__init__(id=id)
        self.components = components


class SidebarPage(Component):
    def __init__(self, sidebar: list[Component], main: list[Component], id: str = None):
        super().__init__(id=id)
        self.sidebar = sidebar
        self.main = main


class Chart(Component):
    def __init__(
        self,
        state: "DemandModellingState",
        renderer: Callable[["DemandModellingState", "..."], go.Figure],
        render_args: dict = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.__state = state
        self.__renderer = renderer
        self.__render_args = render_args or {}

    @property
    def chart(self):
        try:
            chart = self.__renderer(self.__state, **self.__render_args)
        except:
            logger.exception("Error rendering chart")
            chart = placeholder("Error rendering chart")
        if isinstance(chart, go.Figure):
            chart = plotly.io.to_json(chart, pretty=False)
        else:
            raise ValueError("Renderer must return a plotly.graph_objects.Figure")
        return chart


class Expando(Component):
    def __init__(self, *components: Component, title: str, id: str = None):
        super().__init__(id=id)
        self.title = title
        self.components = components


class DateSelect(Component):
    def __init__(self, id: str, title: str):
        super().__init__(id=id)
        self.title = title


class TextField(Component):
    def __init__(
        self,
        id: str,
        title: str,
        input_props: dict = None,
        start_icon: str = None,
        end_icon: str = None,
    ):
        super().__init__(id=id)
        self.title = title
        self.input_props = input_props or {}
        self.start_icon = start_icon
        self.end_icon = end_icon


class Select(Component):
    def __init__(
        self,
        id: str,
        title: str,
        options: List[Dict[str, str]],
        auto_action: Optional[str] = None,
    ):
        super().__init__(id=id)
        self.title = title
        self.options = options or []
        self.auto_action = auto_action


class Fragment(Component):
    def __init__(self, *components: Component, padded: bool = False):
        super().__init__(type_name="fragment")
        self.components = components
        if padded:
            self.padded = True


class FileUpload(Component):
    def __init__(self, id: str, title: str, action: str):
        super().__init__(id=id)
        self.title = title
        self.action = action
