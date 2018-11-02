from decimal import *
import json

from django.http import JsonResponse
from rest_framework.decorators import api_view

from ipware import get_client_ip

from project import settings
from speedtest_api.services import transactions


@api_view(['GET'])
def generate_random_transaction(request):
    """
    Generate a new random transaction and return its basic information

    @param request The REST request to the endpoint
    @return JsonResponse The general transaction information including the id, wallets, wallet locations, amount, and ip

    """

    client_ip, is_routable = get_client_ip(request)

    transaction = transactions.new_transaction_random(client_ip)
    origin_node = transaction.origin.wallet.node
    destination_node = transaction.destination.wallet.node

    origin = {
        'id': origin_node.id,
        'nodeLocation': settings.NODE_LOCATIONS[origin_node.id],
        'latitude': origin_node.latitude,
        'longitude': origin_node.longitude
    }

    destination = {
        'id': destination_node.id,
        'nodeLocation': settings.NODE_LOCATIONS[destination_node.id],
        'latitude': destination_node.latitude,
        'longitude': destination_node.longitude
    }

    #  Convert from RAW to nano and round to four decimal places
    amount_decimal = Decimal(transaction.amount) / Decimal(1e24)
    amount = round(amount_decimal, 4)

    random_transaction = {
        "id": transaction.id,
        "origin": origin,
        "destination": destination,
        "amount": amount,
        "ip": client_ip
    }

    return JsonResponse(random_transaction)


@api_view(['POST'])
def send_transaction(request):
    """
    Send the transaction generated in the initial transaction generation

    @param request The REST request to the endpoint
    @return JsonResponse The transaction timing information

    """
    body = json.loads(request.body)
    transaction_id = body['id']

    transaction = transactions.get_transaction(transaction_id)

    if transaction is None:
        return JsonResponse({'message': 'Transaction ' + str(transaction_id) + ' not found.'}, status=404)

    elif transaction.start_send_timestamp is not None:
        return JsonResponse({'message': 'Transaction ' + str(transaction_id) + ' has already been sent.'}, status=403)

    else:
        sent_transaction = transactions.send_transaction(transaction)

        transaction_stats = {
            'id': sent_transaction.id,
            'start': sent_transaction.start_send_timestamp,
            'end': sent_transaction.end_receive_timestamp
        }

        return JsonResponse(transaction_stats, status=200)
