from myojin.submodule import Module

module = Module(__name__, url_prefix="")
from . import views
for name, submodule in views.__dict__.items():
    if not name.startswith("_") and hasattr(submodule,"module"):
        submodule.module.register_to(module)
## from myojin.submodule import Module

## module = Module(__name__, url_prefix="")
## from . import views
## views.top.module.register_to(module)
## views.crud.module.register_to(module)
## views.sproxtest.module.register_to(module)
