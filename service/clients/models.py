from django.contrib.auth import get_user_model
from django.db import models


class Client(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    company_name = models.CharField(max_length=100)
    full_address = models.CharField(max_length=100)

    def __str__(self):
        return f'Client: {self.company_name}'