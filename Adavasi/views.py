from django.shortcuts import render, redirect
import datetime
import requests
import json


def homeView(request):
    return render(request, 'home.html')


def productView(request):
        product = {
            'name': 'Adivasi Hakki Pikki Hair Oil (Original) COD (Cash On Delivery) + Free Delivery',
            'description': 'Hakki Pikki Adivasi Herbal Hair Oil is crafted from 108 herbal ingredients...',
            'image_url': 'Hakki.jpg',
            'sub_products': [
                {'size': '250ML (45 Days Course)', 'price': 799, 'discounted_price': 1200, 'currency': '₹'},
                {'size': '500ML (3 Months Course) #BestSeller', 'price': 1200, 'discounted_price': 2100, 'currency': '₹'},
                {'size': '1L (6 Months Course)', 'price': 2499, 'discounted_price': 3499, 'currency': '₹'},
                
            ],
            'buy_link': '#',
        }

        selected_size = request.GET.get('size', '500ML (3 Months Course) #BestSeller')
        selected_sub_product = next((sub for sub in product['sub_products'] if sub['size'] == selected_size), None)
        cart = request.session.get('cart', [])
        if not isinstance(cart, list):
            cart = []

        if request.method == 'POST':
            size = request.POST.get('size')
            quantity = int(request.POST.get('quantity', 1))

            sub_product = next((sub for sub in product['sub_products'] if sub['size'] == size), None)

            if sub_product:
                for item in cart:
                    if isinstance(item, dict) and item.get('size') == size:
                        item['quantity'] += quantity
                        break
                else:
                    cart.append({
                        'name': product['name'],
                        'size': sub_product['size'],
                        'price': sub_product['price'],
                        'quantity': quantity,
                        'currency': sub_product['currency']
                    })
                request.session['cart'] = cart
                request.session.modified = True

            return redirect('cart_view')

        context = {
            'product': product,
            'selected_sub_product': selected_sub_product,
            'selected_size': selected_size,
        }

        return render(request, 'product.html', context)


def cartView(request):
    cart = request.session.get('cart', [])
    if not isinstance(cart, list):
        cart = []

    grand_total = {
        'amount': 0,
        'currency': '₹'  
    }

    for item in cart:
        if isinstance(item, dict):
            item['total'] = item['price'] * item['quantity'] 
            grand_total['amount'] += item['total']

    if request.method == 'POST':
        size_to_remove = request.POST.get('size')
        cart = [item for item in cart if isinstance(item, dict) and item['size'] != size_to_remove]
        
        request.session['cart'] = cart
        request.session.modified = True
        grand_total['amount'] = sum([item['price'] * item['quantity'] for item in cart])

    context = {
        'cart': cart,
        'grand_total': grand_total
    }
    return render(request, 'cart.html', context)



def get_shiprocket_token():
    url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    payload = {
        "email": "email", 
        "password": "password"  
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise Exception("Failed to authenticate with Shiprocket")


def create_shiprocket_order(order_data):
    token = get_shiprocket_token()
    
    url = "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, json=order_data, headers=headers)
    
    print(f"Order API Response: {response.status_code}, {response.json()}")  # Log the response

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Order creation failed: {response.json()}")
    

def checkoutView(request):
        cart = request.session.get('cart', [])
    
        if not cart:
            return redirect('cart_view')

        if request.method == 'POST':
            billing_first_name = request.POST.get('first_name')
            billing_last_name = request.POST.get('last_name')  
            billing_address = request.POST.get('address')
            billing_pincode = request.POST.get('pincode')
            billing_city = request.POST.get('city', 'Delhi')
            billing_state = request.POST.get('state', 'Delhi')
            billing_country = request.POST.get('country', 'India')
            billing_phone = request.POST.get('phone')

            # Generate order ID and order date
            order_id = f"ORDER{int(datetime.datetime.now().timestamp())}"
            order_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            order_data = {
                "order_id": order_id,
                "order_date": order_date,
                "pickup_location": "Primary",  
                "billing_customer_name": billing_first_name,
                "billing_last_name": billing_last_name,
                "billing_address": billing_address,
                "billing_city": billing_city,
                "billing_pincode": billing_pincode,
                "billing_state": billing_state,
                "billing_country": billing_country,
                "billing_phone": billing_phone,
                "shipping_is_billing": True,
                "order_items": [
                    {
                        "name": item["size"],
                        "sku": f"hair-oil-{item['size']}",
                        "units": item["quantity"],
                        "selling_price": item["price"],
                        "discount": 0,
                        "tax": 0,  
                        "hsn": 441122  
                    } for item in cart
                ],
                "payment_method": "COD",
                "sub_total": sum(item['price'] * item['quantity'] for item in cart),
                "length": 10,
                "breadth": 10,
                "height": 10,
                "weight": 0.5
            }

            try:
                response = create_shiprocket_order(order_data)

                del request.session['cart']

                request.session['order_details'] = order_data

                return redirect('confirmed')

            except Exception as e:
                return render(request, 'checkout.html', {'error': str(e)})

        return render(request, 'checkout.html')


def orderConfirmedView(request):
    order_details = request.session.get('order_details')

    if not order_details:
        return redirect('home')  

    del request.session['order_details']

    return render(request, 'orderconfirmed.html', {'order': order_details})