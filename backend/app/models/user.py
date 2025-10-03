from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class User(Model):
    id = fields.IntField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True)
    name = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"
