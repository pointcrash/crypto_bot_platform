from decimal import Decimal, InvalidOperation, DivisionUndefined

# Пример данных
psn_cost_after_loss = Decimal('0')
psn_qty = Decimal('0')  # Деление на ноль вызывает ошибку DivisionUndefined


trigger_price = psn_cost_after_loss / psn_qty

