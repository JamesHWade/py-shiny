__all__ = (
    "ReactiveValuesProxy",
    "OutputsProxy",
    "SessionProxy",
    "ShinyModule",
)

from typing import Optional, Union, Callable, Any

from htmltools.core import TagChildArg

from .session import Session, Outputs, _require_active_session
from .reactives import ReactiveValues
from .render import RenderFunction


class ReactiveValuesProxy(ReactiveValues):
    def __init__(self, ns: str, values: ReactiveValues):
        self._ns: str = ns
        self._values: ReactiveValues = values

    def _ns_key(self, key: str) -> str:
        return self._ns + "-" + key

    def __setitem__(self, key: str, value: object) -> None:
        self._values[self._ns_key(key)] = value

    def __getitem__(self, key: str) -> object:
        return self._values[self._ns_key(key)]

    def __delitem__(self, key: str) -> None:
        del self._values[self._ns_key(key)]


class OutputsProxy(Outputs):
    def __init__(self, ns: str, outputs: Outputs):
        self._ns: str = ns
        self._outputs: Outputs = outputs

    def _ns_key(self, key: str) -> str:
        return self._ns + "-" + key

    def __call__(
        self, name: str
    ) -> Callable[[Union[Callable[[], object], RenderFunction]], None]:
        return self._outputs(self._ns_key(name))


class SessionProxy(Session):
    def __init__(self, ns: str, parent_session: Session) -> None:
        self._ns: str = ns
        self._parent: Session = parent_session
        self.input: ReactiveValuesProxy = ReactiveValuesProxy(ns, parent_session.input)
        self.output: OutputsProxy = OutputsProxy(ns, parent_session.output)


class ShinyModule:
    def __init__(
        self,
        ui: Callable[..., TagChildArg],
        server: Callable[[SessionProxy], None],
    ) -> None:
        self._ui: Callable[..., TagChildArg] = ui
        self._server: Callable[[SessionProxy], None] = server

    def ui(self, namespace: str, *args: Any) -> TagChildArg:
        ns = ShinyModule._make_ns_fn(namespace)
        return self._ui(ns, *args)

    def server(self, ns: str, *, session: Optional[Session] = None) -> None:
        self.ns: str = ns
        session = _require_active_session(session)
        session_proxy = SessionProxy(ns, session)
        self._server(session_proxy)

    @staticmethod
    def _make_ns_fn(namespace: str) -> Callable[[str], str]:
        def ns_fn(id: str) -> str:
            return namespace + "-" + id

        return ns_fn
