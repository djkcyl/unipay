import random
import string

from datetime import datetime
from peewee import SqliteDatabase, Model, DateTimeField, CharField, IntegerField


def generate_short_url():
    # 生成短链接
    while True:
        short_url = "".join(random.sample(string.ascii_letters + string.digits, 6))
        if not check_short_id(short_url):
            return short_url


db = SqliteDatabase("database.db")


class BaseModel(Model):
    class Meta:
        database = db


class UniPay(BaseModel):
    created_at = DateTimeField(default=datetime.now)
    short_id = CharField(unique=True, default=generate_short_url)
    alipay = CharField()
    wechatpay = CharField()
    scan_count = IntegerField(default=0)

    class Meta:
        db_table = "unipay"


db.create_tables([UniPay])


def check_short_id(short_id):
    return UniPay.get_or_none(UniPay.short_id == short_id)


def add_unipay(alipay, wechatpay) -> UniPay:
    return UniPay.create(alipay=alipay, wechatpay=wechatpay)


def get_unipay(short_id) -> UniPay | None:
    unipay: UniPay | None = UniPay.get_or_none(UniPay.short_id == short_id)
    if unipay:
        unipay.scan_count += 1
        unipay.save()
    return unipay