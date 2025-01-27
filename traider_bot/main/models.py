from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('CONTRACT', 'CONTRACT'),
        ('UNIFIED', 'UNIFIED'),
    )

    LOW_MARGIN_ACTIONS_CHOICES = (
        ('alert', 'Только уведомление'),
        ('off_bots', 'Выключить ботов'),
    )

    LOW_MARGIN_VALUE_CHOICES = (
        ('$', '$'),
        ('%', '%'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(unique=True, max_length=25)
    service = models.ForeignKey('ExchangeService', on_delete=models.SET_NULL, null=True)
    API_TOKEN = models.CharField(max_length=255)
    SECRET_KEY = models.CharField(max_length=255)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='UNIFIED', null=True)
    is_mainnet = models.BooleanField()
    url = models.CharField(default='https://api-testnet.bybit.com', max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)

    margin_alert_is_active = models.BooleanField(default=False)
    low_margin_value = models.IntegerField(blank=True, null=True)
    low_margin_value_type = models.CharField(max_length=10, choices=LOW_MARGIN_VALUE_CHOICES, default='$', null=True, blank=True)
    low_margin_actions = models.CharField(max_length=255, choices=LOW_MARGIN_ACTIONS_CHOICES, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_mainnet:
            self.url = 'https://api.bybit.com'
        else:
            self.url = 'https://api-testnet.bybit.com'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WhiteListAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='whitelist')
    address = models.CharField()
    symbol = models.CharField(max_length=25, blank=True)
    chain = models.CharField(max_length=25, blank=True)
    note = models.CharField(max_length=25, blank=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)


class ActiveBot(models.Model):
    bot_id = models.CharField()


class ExchangeService(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name


class WSManager(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, null=True)
    status = models.BooleanField()
    error_text = models.CharField(null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account.name


class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral')
    code = models.CharField(max_length=20, unique=True)
    referred_users = models.ManyToManyField(User, related_name='referred_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.code}'

    def generate_code(self):
        import string, random
        characters = string.ascii_letters + string.digits
        self.code = ''.join(random.choice(characters) for _ in range(10))

    def save(self, *args, **kwargs):
        if not self.code:
            self.generate_code()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_referral(sender, instance, created, **kwargs):
    if created:
        Referral.objects.create(user=instance)


class AccountBalance(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='accountbalance')
    asset = models.CharField(max_length=25, default='USDT')
    balance = models.CharField(max_length=25, null=True, blank=True)
    available_balance = models.CharField(max_length=25, null=True, blank=True)
    margin = models.CharField(max_length=25, null=True, blank=True)
    un_pnl = models.CharField(max_length=25, null=True, blank=True)

    time_create = models.DateTimeField(null=True, blank=True)
    time_update = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.margin and self.balance and self.available_balance:
            try:
                self.margin = str(round(float(self.balance) - float(self.available_balance), 2))
            except ValueError:
                self.margin = '0'
        elif self.margin:
            self.margin = str(round(float(self.margin), 2))

        if not self.time_create:
            self.time_create = timezone.now()

        self.time_update = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.account.name


class AccountHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='accounthistory')
    symbol = models.CharField(max_length=25)
    side = models.CharField(max_length=25, blank=True, null=True)
    order_id = models.CharField(max_length=50, blank=True, null=True)
    change = models.CharField(max_length=25)
    cash_flow = models.CharField(max_length=25, blank=True, null=True)
    fee = models.CharField(max_length=25, blank=True, null=True)
    transaction_time = models.CharField(max_length=30)
    type = models.CharField(max_length=25)

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.account.name
