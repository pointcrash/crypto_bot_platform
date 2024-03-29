from decimal import Decimal
from django import forms

from api_test.api_v5_bybit import get_query_account_coins_balance, get_current_price
from main.models import Account
from .general_functions import get_quantity_from_price
from .models import Bot, Set0Psn, SimpleHedge, OppositePosition, StepHedge, BotModel


class BotModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.qty = kwargs.pop('initial', None)
        super().__init__(*args, **kwargs)
        if self.request:
            if self.request.user.is_superuser:
                self.fields['account'].queryset = Account.objects.all()
            else:
                self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)

    class Meta:
        model = BotModel

        fields = ['account', 'symbol', 'leverage', 'amount_long', 'amount_short', 'margin_type']

        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'leverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_long': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_short': forms.NumberInput(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),

        }

        labels = {
            'account': 'Аккаунт',
            'symbol': 'Торговая пара',
            'leverage': 'Плечо',
            'amount_long': 'Лонг USDT',
            'amount_short': 'Шорт USDT',
            'margin_type': 'Тип маржи',
        }


class SimpleHedgeForm(forms.ModelForm):
    class Meta:
        model = SimpleHedge
        fields = ['tppp', 'tpap',  'tp_count', ]

        widgets = {
            'tppp': forms.TextInput(attrs={'class': 'form-control'}),
            'tpap': forms.TextInput(attrs={'class': 'form-control'}),
            'tp_count': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'tppp': 'TP Price % (TPPP)',
            'tpap': 'TP Amount % (TPAP)',
            'tp_count': 'TP Count',
        }

    def clean(self):
        cleaned_data = super().clean()
        tpap = cleaned_data.get('tpap')
        tp_count = cleaned_data.get('tp_count')

        if float(tpap) * tp_count > 100:
            raise forms.ValidationError(f"Произведение значений TP Amount = {tpap} и TP Count = {tp_count} не может превышать 100%."
                                        f" Текущий результат = {float(tpap) * tp_count}")


class Set0PsnForm(forms.ModelForm):
    class Meta:
        TREND_CHOICE = (
            (1, '1'),
            (1, '2'),
            (3, '3'),
        )

        model = Set0Psn
        fields = ['set0psn', 'trend', 'limit_pnl_loss_s0n', 'max_margin_s0p']

        widgets = {
            'trend': forms.Select(choices=TREND_CHOICE, attrs={'class': 'form-control'}),
            'limit_pnl_loss_s0n': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '-100'}),
            'max_margin_s0p': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'set0psn': 'Activate',
            'trend': 'Trend (%)',
            'limit_pnl_loss_s0n': 'Limit PNL loss',
            'max_margin_s0p': 'Max Margin',

        }

    def clean(self):
        cleaned_data = super().clean()
        limit_pnl = cleaned_data.get('limit_pnl_loss_s0n')

        if limit_pnl:
            if '-' not in limit_pnl:
                raise forms.ValidationError(
                    "Invalid 'Limit PNL loss' value. Value must consist of numbers only and contain a sign '-'")

        return cleaned_data


class OppositePositionForm(forms.ModelForm):
    class Meta:
        model = OppositePosition
        fields = ['activate_opp', 'limit_pnl_loss_opp', 'max_margin_opp', 'psn_qty_percent_opp']

        widgets = {
            'limit_pnl_loss_opp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '-100'}),
            'max_margin_opp': forms.TextInput(attrs={'class': 'form-control'}),
            'psn_qty_percent_opp': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'activate_opp': 'Activate',
            'limit_pnl_loss_opp': 'Limit PNL loss',
            'psn_qty_percent_opp': 'Quantity (%)',
            'max_margin_opp': 'Max Margin',
        }

    def clean(self):
        cleaned_data = super().clean()
        limit_pnl = cleaned_data.get('limit_pnl_loss_opp')

        if limit_pnl:
            if '-' not in limit_pnl:
                raise forms.ValidationError(
                    "Invalid 'Limit PNL loss' value. Value must consist of numbers only and contain a sign '-'")

        return cleaned_data


class BotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.qty = kwargs.pop('initial', None)
        super().__init__(*args, **kwargs)
        if self.qty:
            print(self.qty)
            print('__________________________________________________________')
            self.fields['qty'] = self.qty

        if self.request:
            if self.request.user.is_superuser:
                self.fields['account'].queryset = Account.objects.all()
            else:
                self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)

        self.fields['side'].required = False
        self.fields['orderType'].required = False
        self.fields['interval'].required = False
        self.fields['grid_avg_value'].required = False
        self.fields['chw'].required = False
        self.fields['deviation_from_lines'].required = False
        self.fields['bb_avg_percent'].required = False
        self.fields['dfm'].required = False
        self.fields['take_on_ml_percent'].required = False
        self.fields['price'].required = False

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'qty_kline', 'd', 'auto_avg', 'bb_avg_percent',
                  'deviation_from_lines',
                  'is_percent_deviation_from_lines', 'dfm',
                  'chw', 'dfep', 'max_margin', 'take_on_ml', 'take_on_ml_percent', 'time_sleep', 'repeat',
                  'grid_avg_value', 'bin_order',  'price', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'take_on_ml_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfm': forms.NumberInput(attrs={'class': 'form-control'}),
            'chw': forms.NumberInput(attrs={'class': 'form-control'}),
            'dfep': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Market'}),
        }

        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'interval': 'Candle Interval',
            'qty_kline': 'Periods',
            'd': 'Deviation',
            'auto_avg': 'Auto Average',
            'take_on_ml': 'Middle Line',
            'take_on_ml_percent': '%',
            'bb_avg_percent': 'Average Percent',
            'is_percent_deviation_from_lines': '%',
            'deviation_from_lines': '(± BB Deviation)',
            'dfm': 'DFM',
            'chw': 'ChW',
            'dfep': 'DFEP',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'repeat': 'Repeat Cycle',
            'grid_avg_value': 'Two-Sided mode: Profit/Avg Value (%)',
            'bin_order': 'Turn after ML',
            'price': 'Price',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        account = cleaned_data.get('account')
        side = cleaned_data.get('side')
        deviation_from_lines = cleaned_data.get('deviation_from_lines')
        is_percent_deviation_from_lines = cleaned_data.get('is_percent_deviation_from_lines')
        symbol = cleaned_data.get('symbol')
        qty_USDT = cleaned_data.get('qty')
        leverage = cleaned_data.get('isLeverage')

        if qty_USDT is None:
            raise forms.ValidationError("Invalid '1st order investments' value. Only whole numbers")

        if order_type == 'Market' and side == 'FB':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'First Band'.")

        # if deviation_from_lines:
        #     if not is_percent_deviation_from_lines and deviation_from_lines < Decimal(symbol.minPrice):
        #         raise forms.ValidationError(f"Minimum '± BB Deviation' value = {symbol.minPrice}")

        current_price = get_current_price(account, 'linear', symbol)
        qty = get_quantity_from_price(qty_USDT, current_price, symbol.minOrderQty, leverage)

        if qty < Decimal(symbol.minOrderQty) or qty > Decimal(symbol.maxOrderQty):
            raise forms.ValidationError(
                f"Допустимые значения '1st order investment': min = {Decimal(symbol.minOrderQty) / leverage}, max = {Decimal(symbol.maxOrderQty) / leverage}")

        # if leverage > Decimal(symbol.maxLeverage) or leverage < Decimal(symbol.minLeverage):
        #     raise forms.ValidationError(
        #         f"Допустимые значения плеча: min = {symbol.minLeverage}, max = {symbol.maxLeverage}")
        #
        # if side == 'TS':
        #     raise forms.ValidationError('Режим "TS" еще не реализован для стратегии Боллинджера')

        return cleaned_data


class GridBotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            if self.request.user.is_superuser:
                self.fields['account'].queryset = Account.objects.all()
            else:
                self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)

    #     self.fields['account'].label_from_instance = self.label_from_instance
    #
    # @staticmethod
    # def label_from_instance(obj):
    #     balance = get_query_account_coins_balance(obj)
    #     try:
    #         for elem in balance:
    #             if elem['coin'] == 'USDT':
    #                 return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
    #     except:
    #         return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'side', 'interval', 'isLeverage', 'margin_type', 'orderType', 'qty',
                  'auto_avg', 'grid_avg_value', 'grid_profit_value', 'bb_avg_percent',
                  'deviation_from_lines', 'is_percent_deviation_from_lines', 'max_margin', 'qty_kline', 'd',
                  'time_sleep', 'repeat', 'grid_take_count', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            # 'category': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'orderType': forms.Select(attrs={'class': 'form-control'}),
            'margin_type': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'interval': forms.Select(attrs={'class': 'form-control'}),
            'qty_kline': forms.NumberInput(attrs={'class': 'form-control'}),
            'd': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_profit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_take_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'deviation_from_lines': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            # 'category': 'Category',
            'symbol': 'Symbol',
            'side': 'Side',
            'margin_type': 'Margin',
            'orderType': 'Order Type',
            'isLeverage': 'Leverage',
            'interval': 'Candle Interval',
            'auto_avg': 'Auto Average',
            'grid_avg_value': 'Grid Average Value (%)',
            'grid_profit_value': 'Grid Profit Value (%)',
            'grid_take_count': 'Takes Count',
            'bb_avg_percent': 'Average Percent',
            'deviation_from_lines': '± BB Deviation',
            'is_percent_deviation_from_lines': '%',
            'qty_kline': 'Periods',
            'd': 'Deviation',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'repeat': 'Repeat Cycle',
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('orderType')
        side = cleaned_data.get('side')
        deviation_from_lines = cleaned_data.get('deviation_from_lines')
        is_percent_deviation_from_lines = cleaned_data.get('is_percent_deviation_from_lines')
        symbol = cleaned_data.get('symbol')
        qty = cleaned_data.get('qty')
        orderType = cleaned_data.get('orderType')
        auto_avg = cleaned_data.get('auto_avg')
        margin = cleaned_data.get('max_margin')
        leverage = cleaned_data.get('isLeverage')

        # if not margin and auto_avg:
        #     raise forms.ValidationError("Значение 'Max Margin' не может быть пустым")

        if qty is None:
            raise forms.ValidationError(
                "Значение '1st order investments' неверно. Поле не может быть пустым или иметь дробные значения")

        if order_type == 'Market' and side == 'Auto':
            raise forms.ValidationError("Invalid combination: orderType - 'Market' cannot have side - 'Auto'.")

        # if deviation_from_lines:
        #     if not is_percent_deviation_from_lines and deviation_from_lines < Decimal(symbol.minPrice):
        #         raise forms.ValidationError(f"Minimum '± BB Deviation' value = {symbol.minPrice}")

        # elif not deviation_from_lines and orderType == "Limit":
        #     raise forms.ValidationError("If 'Order Type' - Limit, '± BB Deviation' must be filled")

        if qty < Decimal(symbol.minOrderQty) or qty > Decimal(symbol.maxOrderQty):
            raise forms.ValidationError(
                f"Допустимые значения '1st order investment': min = {symbol.minOrderQty}, max = {symbol.maxOrderQty}")

        if leverage > Decimal(symbol.maxLeverage) or leverage < Decimal(symbol.minLeverage):
            raise forms.ValidationError(
                f"Допустимые значения плеча: min = {symbol.minLeverage}, max = {symbol.maxLeverage}")

        return cleaned_data


class HedgeGridBotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            if self.request.user.is_superuser:
                self.fields['account'].queryset = Account.objects.all()
            else:
                self.fields['account'].queryset = Account.objects.filter(owner=self.request.user)
        self.fields['account'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        balance = get_query_account_coins_balance(obj)
        try:
            for elem in balance:
                if elem['coin'] == 'USDT':
                    return f"{obj.name} - {round(Decimal(elem['transferBalance']), 1)} USDT"
        except:
            return f"{obj.name} error"

    class Meta:
        model = Bot
        fields = ['account', 'symbol', 'isLeverage', 'qty', 'grid_avg_value', 'grid_profit_value', 'max_margin',
                  'time_sleep', 'bb_avg_percent', ]

        widgets = {
            'qty': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'symbol': forms.Select(attrs={'class': 'form-control'}),
            'isLeverage': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_avg_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'bb_avg_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'grid_profit_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_margin': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_sleep': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'qty': '1st order investments $',
            'account': 'Account',
            'symbol': 'Symbol',
            'isLeverage': 'Leverage',
            'grid_avg_value': 'Grid Average Value (%)',
            'grid_profit_value': 'Grid Profit Value (%)',
            'max_margin': 'Max Margin',
            'time_sleep': 'Request Rate (sec)',
            'bb_avg_percent': 'Average Percent',
        }

