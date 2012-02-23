from .mapper_imports import *

mapper(
    Memo, memo, extension=MyojinMapperExt(),
    order_by=memo.c.id,
    properties=dict(
        user=relation(User),
        )
    )
from sqlalchemy.orm import mapper, relationship, column_property

mapper(
    User, user, extension=MyojinMapperExt(),
    order_by=user.c.id,
    properties=dict(
        memos=relation(Memo,primaryjoin=and_(
            memo.c.user_id==user.c.id,~memo.c.deleted
            )),
        ))



mapper(
    Image, image, extension=MyojinMapperExt(),
    order_by=image.c.id,
    properties=dict(
        ))



