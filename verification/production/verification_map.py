from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime


# Include the `fusioncharts.py` file that contains functions to embed the charts.
from ..fusioncharts import FusionCharts

from ..models import *
from ..forms import *

def map(request):
    mb_token = 'MY_TOKEN'
    if request.POST.get('meter_id'):
        meter_id = request.POST.get('meter_id')
        # MUST send the data back as a json object, a single value or anything else will not work.
        return JsonResponse({'meter_id': meter_id})
    return render(request, 'verification/map.html',
                  {'mapbox_access_token': mb_token})


def map_plus_chart(request, user_selected_site, user_selected_start, user_selected_end):
    mb_token = 'MY_TOKEN'
    # Chart data is passed to the `dataSource` parameter, as dict, in the form of key-value pairs.
    dataSource = {}

    if request.method == 'POST':
        if request.POST.get('meter_id'):
            user_selected_site = request.POST.get('meter_id')

    dataSource['chart'] = {
        "caption": "Forecast Errors For " + user_selected_site + " Made " + user_selected_start + " days ago from ",
        "theme": "fusion",
        "showLegend": "1",
        # "yAxisMaxValue": "50",
        # "yAxisMinValue": "0",
        "interactiveLegend": "1",
        "drawAnchors": "1"
    }

    #station_ids = ['MFAC1', 'NMFC1', 'RUFC1', 'actual']
    station_ids = [user_selected_site]
    dataSource['dataset'] = []
    dataSource['linkeddata'] = []
    dataSource['dataset'] = []
    dataSource['categories'] = []

    for station_id in station_ids:
        categories = {}
        categories['category'] = []
        dataset = {}
        dataset['data'] = []
        dataset['seriesname'] = station_id
        database = database_pull(dataset, categories, user_selected_start, user_selected_end, station_id)
        dataSource['dataset'].append(database[0])
    dataSource['categories'].append(database[1])

    line2D = FusionCharts("zoomline", "myChart", "800", "600", "chart-1", "json", dataSource)

    if request.POST.get('meter_id'):
        # meter_id = request.POST.get('meter_id')
        # MUST send the data back as a json object, a single value or anything else will not work.
        return JsonResponse(dataSource)
    return render(request, 'verification/map_and_chart.html',
                  {'mapbox_access_token': mb_token,'output': line2D.render(), 'chartTitle': 'Day '})


def database_pull(dataset, categories, user_selected_start, user_selected_end, station_id):
    for key in Forecasts.objects.pcwa_metered(station_id, user_selected_start):
    #for key in Forecasts.objects.test():
        data = {}
        category = {}
        category['label'] = key.date_valid.strftime("%m-%d-%Y")
        data['value'] = getattr(key, station_id)

        dataset['data'].append(data)
        categories['category'].append(category)
    return (dataset, categories)