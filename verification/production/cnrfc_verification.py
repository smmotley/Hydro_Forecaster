from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime


# Include the `fusioncharts.py` file that contains functions to embed the charts.
from ..fusioncharts import FusionCharts

from ..models import *
from ..forms import *


# The `chart` function is defined to load data from a Python Dictionary. This data will be converted to
# JSON and the chart will be rendered.

def chart(request, user_selected_site, user_selected_start, model, user_selected_end):

    forecast_type = 'daily_comparison'

    if request.method == 'POST':
        if request.POST.get('station_dropdown'):
            user_selected_site = request.POST.get('station_dropdown')
        if request.POST.get('forecaster_dropdown'):
            model = request.POST.get('forecaster_dropdown')
        if request.POST.get('start_date'):
            user_selected_start = request.POST.get('start_date') + " 00:00:00"
        if request.POST.get('end_date'):
            user_selected_end = request.POST.get('end_date') + " 00:00:00"
        if request.POST.get('clicked_date'):
            clicked_date = datetime.strptime(request.POST.get('clicked_date') + "-" + str(datetime.now().year), '%m-%d-%Y')
            user_selected_date = clicked_date.strftime("%Y-%m-%d") + " 00:00:00"
            forecast_type = 'single_day'



    # Chart data is passed to the `dataSource` parameter, as dict, in the form of key-value pairs.
    dataSource = {}

    dataSource['chart'] = {
        "caption": "Forecast Errors For " + user_selected_site +" Made " + user_selected_start +" days ago from " + model,
        "theme": "fusion",
        "showLegend": "1",
        #"yAxisMaxValue": "50",
        #"yAxisMinValue": "0",
        "interactiveLegend": "1",
        "drawAnchors": "1"
    }

    # Convert the data in the `actualData` array into a format that can be consumed by FusionCharts.
    # The data for the chart should be in an array wherein each element of the array is a JSON object
    # having the `label` and `value` as keys.

    # Main Keys
    city_ids = []
    #models = ['MFAC1', 'GFS', 'EURO', 'EURO_EPS', 'GFS_bc', 'NWS', 'actual']
    cnrfc_ids = ['MFAC1', 'NMFC1', 'RUFC1','actual']
    dataSource['dataset'] = []
    dataSource['linkeddata'] = []
    dataSource['dataset'] = []
    dataSource['categories'] = []


    for cnrfc_id in cnrfc_ids:
        categories = {}
        categories['category'] = []
        dataset = {}
        dataset['data'] = []
        dataset['seriesname'] = cnrfc_id
        database = database_pull(dataset, categories, user_selected_start, user_selected_end, cnrfc_id, forecast_type)
        dataSource['dataset'].append(database[0])
    dataSource['categories'].append(database[1])

    #city_ids = list(Forecasts.objects.values_list('city_code', flat=True).distinct())

    # Create an object for the Column 2D chart using the FusionCharts class constructor
    #column2D = FusionCharts("column3D", "ex1", "400", "500", "chart-1", "json", dataSource)
    line2D = FusionCharts("zoomline", "myChart", "800", "600", "chart-1", "json", dataSource)
    line2D.addEvent("dataplotClick","onDataplotClick")

    # If the request to render is coming from a POST request where a line was clicked, send the
    # appropirate data back in a JSON response (This will prevent the entire page from re-rendering).

    if request.POST.get('clicked_date'):
        return JsonResponse(dataSource)
    return render(request, 'verification/performance.html', {'form': DateRangeForm(), 'output': line2D.render(),
                                                       'chartTitle': 'Day ' + user_selected_start + ' Forecast Errors For ' + user_selected_site,
                                                        'cnrfc_ids': cnrfc_ids,
                                                        })

def json_builder(data):
    return

def database_pull(dataset, categories, user_selected_start, user_selected_end, station_id, forecast_type):
    if forecast_type == 'daily_comparison':
        for key in Forecasts.objects.cnrfc_vs_metered(user_selected_start,user_selected_end, station_id):
            data = {}
            category = {}
            category['label'] = key.date_valid.strftime("%m-%d-%Y")
            data['value'] = getattr(key, station_id)

            dataset['data'].append(data)
            categories['category'].append(category)
    if forecast_type == 'single_day':
        for key in Forecasts.objects.raw(
                "SELECT 1 as id, a.high as actual, f.PCWA, f.NWS, f.GFS_bc, f.GFS, f.EURO, f.EURO_EPS, "
                "f.date_valid, f.date_created, f.forecast_day, f.city_code "
                "FROM forecasts as f "
                "JOIN actuals AS a ON f.date_valid=a.date_valid And f.city_code = a.station "
                "WHERE f.date_valid = %s  AND f.city_code = %s",
                [user_selected_date, user_selected_start]):
            data = {}
            category = {}
            category['label'] = key.date_valid.strftime("%m-%d")
            data['value'] = getattr(key, model)

            dataset['data'].append(data)
            categories['category'].append(category)

    return (dataset, categories)