from fastapi_amis_admin.amis.components import ColumnImage, InputImage
from fastapi_amis_admin.crud.parser import LabelField
from fastapi_amis_admin.models.fields import Field
from fastapi_amis_admin.utils.translation import i18n as _
from sqlalchemy import ForeignKey, func, select

from fastapi_user_auth.mixins.models import (  # noqa F401
    CreateTimeMixin,
    CUDTimeMixin,
    DeleteTimeMixin,
    EmailMixin,
    PasswordMixin,
    PkMixin,
    UpdateTimeMixin,
    UsernameMixin,
)
from fastapi_user_auth.utils.sqlachemy_adapter import CasbinRule


class BaseUser(PkMixin, CUDTimeMixin, UsernameMixin, PasswordMixin, EmailMixin):
    __tablename__ = "auth_user"
    is_active: bool = Field(default=True, title=_("Is Active"))
    nickname: str = Field(None, title=_("Nickname"), max_length=40)
    avatar: str = Field(
        None,
        title=_("Avatar"),
        max_length=255,
        amis_form_item=InputImage(maxLength=1, maxSize=2 * 1024 * 1024),
        amis_table_column=ColumnImage(width=50, height=50, enlargeAble=True),
    )

    @property
    def is_authenticated(self) -> bool:
        return not self.delete_time and self.is_active

    @property
    def display_name(self) -> str:
        return self.nickname or self.username

    @property
    def identity(self) -> str:
        return self.username


class User(BaseUser, table=True):
    """用户"""

    pass


class Role(PkMixin, CUDTimeMixin, table=True):
    """角色"""

    __tablename__ = "auth_role"

    key: str = Field(title="角色标识", max_length=40, unique=True, index=True, nullable=False)
    name: str = Field(default="", title="角色名称", max_length=40)
    desc: str = Field(default="", title="角色描述", max_length=400, amis_form_item="textarea")


"""
SELECT v0, GROUP_CONCAT(t.name) as roles, GROUP_CONCAT(t.key) as role_keys
FROM (select v0, auth_role.name, auth_role.key
      from auth_casbin_rule
               left join auth_role on casbin_rule.v1 = concat('r:', auth_role.key)
      where auth_casbin_rule.ptype = 'g') as t
GROUP BY v0;
"""
# casbin主体拥有的角色列表,使用','分隔.
CasbinSubjectRolesQuery = (
    select(
        CasbinRule.v0.label("subject"),
        func.group_concat(Role.name).label("role_names"),
        func.group_concat(Role.key).label("role_keys"),
    )
    .where(CasbinRule.ptype == "g")
    .outerjoin(Role, CasbinRule.v1 == func.concat("r:", Role.key))
    .group_by(CasbinRule.v0)
    .subquery()
)

UserRoleNameLabel = LabelField(
    CasbinSubjectRolesQuery.c.role_names.label("role_names"),
    field=Field("", title="权限角色"),
)


class LoginHistory(PkMixin, CreateTimeMixin, table=True):
    """用户登录记录"""

    __tablename__ = "auth_login_history"

    user_id: int = Field(None, title="用户ID", sa_column_args=(ForeignKey("auth_user.id", ondelete="CASCADE"),))
    login_name: str = Field("", title="登录名", max_length=20)
    ip: str = Field("", title="登录IP", max_length=20)
    ip_info: str = Field("", title="IP信息", max_length=255)
    client: str = Field("", title="客户端", max_length=20)
    user_agent: str = Field("", title="浏览器", max_length=400)
    login_type: str = Field("", title="登录类型", max_length=20)
    login_status: str = Field("登录成功", title="登录状态", max_length=20, description="登录成功,密码错误,账号被锁定等")
    forwarded_for: str = Field("", title="转发IP", max_length=60)
