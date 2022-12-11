from django.db import models
import jsonfield
from django.db import connection
import datetime

class EC2Instances(models.Model):
    created_date = models.DateTimeField()
    updated_at = models.DateTimeField(default=datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S"))
    instance_id = models.CharField(max_length=200,unique=True)
    instance_type =  models.CharField(max_length=200)
    instance_name = models.CharField(max_length=200,default="")
    instance_state = models.CharField(max_length=200,default="")
    instance_tags = jsonfield.JSONField(default={})
    key_name =  models.CharField(max_length=200)
    internal_ip =  models.CharField(max_length=200)
    external_ip =   models.CharField(max_length=200)

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE {}'.format(cls._meta.db_table))

