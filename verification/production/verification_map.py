from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime


# Include the `fusioncharts.py` file that contains functions to embed the charts.
from ..fusioncharts import FusionCharts

from ..models import *
from ..forms import *

MB_TOKEN = 'pk.eyJ1Ijoic21vdGxleSIsImEiOiJuZUVuMnBBIn0.xce7KmFLzFd9PZay3DjvAA'

def map(request):
    if request.POST.get('meter_id'):
        meter_id = request.POST.get('meter_id')
        # MUST send the data back as a json object, a single value or anything else will not work.
        return JsonResponse({'meter_id': meter_id})
    return render(request, 'verification/map.html',
                  {'mapbox_access_token': MB_TOKEN})


def map_plus_chart(request, user_selected_site, user_selected_start, user_selected_end):
    if request.method == 'POST':
        if request.POST.get('meter_id'):
            user_selected_site = request.POST.get('meter_id')

    stations = {
        "R11": "MFAC1",
        "R10": "NMFC1",
        "R30": "RUFC1",
        "R20": "R20_EST",
        "R4": "FMDC1"
    }

    pcwa_meter = user_selected_site

    try:
        cnrfc_meter = stations[pcwa_meter]
    except:
        cnrfc_meter = "MFAC1"

    # Chart data is passed to the `dataSource` parameter, as dict, in the form of key-value pairs.
    dataSource = {}
    dataSource['chart'] = {
        "caption": "Historical Data For " + user_selected_site + " Starting On " + user_selected_start,
        "theme": "fusion",
        "showLegend": "1",
        # "yAxisMaxValue": "50",
        "yAxisMinValue": "0",
        "interactiveLegend": "1",
        "drawAnchors": "1"
    }

    station_ids = [pcwa_meter, cnrfc_meter]
    if pcwa_meter == "R20":
        station_ids.append("NMFC1","RUFC1","MFAC1")
    dataSource['dataset'] = []
    dataSource['linkeddata'] = []
    dataSource['dataset'] = []
    dataSource['categories'] = []

    # Go Get Data
    sql_query = Forecasts.objects.cnrfc_vs_metered(pcwa_meter, cnrfc_meter, user_selected_start, user_selected_end)
    for station_id in station_ids:
        categories = {}
        categories['category'] = []
        dataset = {}
        dataset['data'] = []
        dataset['seriesname'] = station_id
        for key in sql_query:
            data = {}
            category = {}
            category['label'] = key.date_valid.strftime("%m-%d-%Y %H:%M")
            data['value'] = getattr(key, station_id)
            dataset['data'].append(data)
            categories['category'].append(category)
        dataSource['dataset'].append(dataset)
    dataSource['categories'].append(categories)

    line2D = FusionCharts("zoomline", "myChart", "800", "600", "chart-1", "json", dataSource)

    if request.POST.get('meter_id'):
        # meter_id = request.POST.get('meter_id')
        # MUST send the data back as a json object, a single value or anything else will not work.
        return JsonResponse(dataSource)
    return render(request, 'verification/map_and_chart.html',
                  {'mapbox_access_token': MB_TOKEN,'output': line2D.render(), 'chartTitle': 'Day '})


def database_pull(dataset, categories, user_selected_start, user_selected_end, station_id):
    for key in Forecasts.objects.pcwa_metered(station_id, user_selected_start):
    #for key in Forecasts.objects.test():
        data = {}
        category = {}
        category['label'] = key.date_valid.strftime("%m-%d-%Y %H:%M")
        data['value'] = getattr(key, station_id)

        dataset['data'].append(data)
        categories['category'].append(category)
    return (dataset, categories)