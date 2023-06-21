from django.shortcuts import render, redirect
from .forms import OrderForm


def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            oder = form.save()
            return redirect('home')
    else:
        form = OrderForm()
    return render(request, 'create_order.html', {'form': form})
