from myojin.submodule import Module

module = Module(__name__, url_prefix="")
from . import views
views.top.module.register_to(module)
views.crud.module.register_to(module)
views.sproxtest.module.register_to(module)
