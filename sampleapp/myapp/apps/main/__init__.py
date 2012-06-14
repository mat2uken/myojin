from myojin.submodule import Module

module = Module(__name__, url_prefix="")
from . import views
for name, submodule in views.__dict__.items():
    if not name.startswith("_") and hasattr(submodule, "module"):
        submodule.module.register_to(module)
## views.top.module.register_to(module)
