from .mapper_imports import *

mapper(
    UserExit, user_exit, extension=MyojinMapperExt(),
    order_by=user_exit.c.id,
    properties=dict(
        exit_user=relation(User,
            primaryjoin=and_(
                user.c.id==user_exit.c.user_id
            )
        )
    )
)

mapper(
    UserType, user_type, extension=MyojinMapperExt(),
    order_by=user_type.c.id,
    properties=dict(
        )
    )
from sqlalchemy.orm import mapper, relationship, column_property

mapper(
    User, user, extension=MyojinMapperExt(),
    order_by=user.c.id,
    properties=dict(
        ))



