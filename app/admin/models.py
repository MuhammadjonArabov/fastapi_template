# admin/models.py
from sqladmin import ModelView
from app.models.users import User
# Yangi modelni import qilish (masalan)
# from app.models.products import Product

class UserAdmin(ModelView, model=User):
    """User modeli uchun admin ko‘rinishi."""
    column_list = [User.id, User.phone, User.verified, User.role, User.banned]
    column_labels = {
        "id": "Foydalanuvchi ID",
        "phone": "Telefon",
        "verified": "Tasdiqlangan",
        "role": "Rol",
        "banned": "Taqiqlangan",
    }
    # ... (qolgan kod o‘zgarmaydi)

# Yangi model uchun misol
"""
class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price]
    column_labels = {
        "id": "ID",
        "name": "Nomi",
        "price": "Narxi",
    }
    form_create_rules = ["name", "price"]
    form_edit_rules = ["name", "price"]
    icon = "fa-solid fa-shopping-cart"
"""