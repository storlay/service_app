from datetime import datetime

from celery_singleton import Singleton
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.core.cache import cache


@shared_task(base=Singleton)
def set_price(subscription_id: int):
    from services.models import Subscription

    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().filter(pk=subscription_id).annotate(
            annotated_price=F('service__full_price') -
                            F('service__full_price') * F('plan__discount_percent') / 100.00).first()

        subscription.price = subscription.annotated_price
        subscription.save()
    cache.delete(settings.PRICE_CACHE_NAME)


@shared_task(base=Singleton)
def set_comment(subscription_id: int):
    from services.models import Subscription

    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
        subscription.comment = str(datetime.now())
        subscription.save()
    cache.delete(settings.PRICE_CACHE_NAME)
