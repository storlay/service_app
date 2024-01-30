from django.conf import settings
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.db import models

from clients.models import Client
from services.tasks import set_price, set_comment


class Service(models.Model):
    name = models.CharField(max_length=50)
    full_price = models.PositiveIntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__full_price = self.full_price

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if self.full_price != self.__full_price:
            super().save(*args, **kwargs)

            for subscription in self.subscriptions.all():
                set_price.delay(subscription.pk)
                set_comment.delay(subscription.pk)

        return super().save(*args, **kwargs)


class Plan(models.Model):
    PLAN_TYPES = (
        ('full', 'Full'),
        ('student', 'Student'),
        ('discount', 'Discount')
    )

    plan_type = models.CharField(choices=PLAN_TYPES, max_length=10)
    discount_percent = models.PositiveIntegerField(default=0,
                                                   validators=[
                                                       MaxValueValidator(100)
                                                   ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__discount_percent = self.discount_percent

    def __str__(self):
        return f'Type of plan: {self.plan_type}'

    def save(self, *args, **kwargs):

        if self.discount_percent != self.__discount_percent:

            for subscription in self.subscriptions.all():
                set_price.delay(subscription.pk)
                set_comment.delay(subscription.pk)

        return super().save(*args, **kwargs)


class Subscription(models.Model):
    client = models.ForeignKey(Client, related_name='subscriptions', on_delete=models.PROTECT)
    service = models.ForeignKey(Service, related_name='subscriptions', on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name='subscriptions', on_delete=models.PROTECT)
    price = models.PositiveIntegerField(default=0)
    comment = models.CharField(max_length=50, default='', db_index=True)

    # field_a = models.CharField(max_length=50, default='')
    # field_b = models.CharField(max_length=50, default='')

    # class Meta:
    #     indexes = [
    #         models.Index(fields=['field_a', 'field_b'])
    #     ]

    def delete(self, *args, **kwargs):
        cache.delete(settings.PRICE_CACHE_NAME)
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        creating = not bool(self.pk)
        result = super().save(*args, **kwargs)
        if creating:
            set_price.delay(self.pk)
        return result
