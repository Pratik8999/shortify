from sqladmin import ModelView
from app.models import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name, User.email, User.country, User.isactive, User.createdon, User.updatedon]
    column_searchable_list = [User.email, User.country]
    column_sortable_list = [User.id, User.email, User.createdon]
    form_excluded_columns = [User.urls, User.createdon, User.updatedon, User.password]

    