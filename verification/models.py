from __future__ import unicode_literals
from django.db import models
from bootstrap_datepicker.widgets import DatePicker
from django import forms
import json


# # Create your models here.
# class SalesRecord(models.Model):
#     Region = models.CharField(max_length=100)
#     Country = models.CharField(max_length=50)
#     City = models.CharField(max_length=50)
#     TotalSales = models.IntegerField()
#
#     def __unicode__(self):
#         return u'%s %s %s %s' % (self.Region, self.Country, self.City, self.TotalSales)

class Historical(models.Manager):
    def historical_by_forecast_day(self, user_selected_start, user_selected_end, station_id):
        return Forecasts.objects.raw("SELECT 1 as id, a.MFAC1 as actual, f.MFAC1 as MFAC1,"
                           "f.date_valid, ROUND(f.MFAC1-a.MFAC1) as MFAC1_error "
                           "FROM cnrfc_fcst as f "
                           "JOIN cnrfc_actuals AS a ON f.date_valid=a.date_valid "
                           "WHERE f.date_created > %s AND f.date_created < %s "
                           "GROUP BY f.date_valid ORDER BY f.date_valid", [user_selected_start, user_selected_end])

    def cnrfc_vs_metered(self, pcwa_meter, cnrfc_meter, user_selected_start, user_selected_end):
        if pcwa_meter == 'R20':
            return Forecasts.objects.raw(("SELECT 1 as id, (cnrfc.MFAC1 - (cnrfc.NMFC1 + cnrfc.RUFC1))*1000 as R20_EST, "
                                          "metered.R20 ,cnrfc.date_valid, "
                                          "cnrfc.NMFC1 * 1000 as NMFC1, cnrfc.RUFC1 * 1000 as RUFC1, cnrfc.MFAC1 * 1000 as MFAC1 "
                                          "FROM cnrfc_actuals as cnrfc "
                                          "JOIN metered_actuals AS metered ON DATETIME(cnrfc.date_valid,'localtime')=metered.date_valid "
                                          "WHERE cnrfc.date_created > %s AND cnrfc.date_created < %s "
                                          "GROUP BY cnrfc.date_valid ORDER BY cnrfc.date_valid"
                                         ),
                                         [user_selected_start, user_selected_end])
        return Forecasts.objects.raw(("SELECT 1 as id, cnrfc.{} * 1000 as {}, metered.{},"
                                     "cnrfc.date_valid "
                                     "FROM cnrfc_actuals as cnrfc "
                                     "JOIN metered_actuals AS metered ON DATETIME(cnrfc.date_valid,'localtime')=metered.date_valid "
                                     "WHERE cnrfc.date_created > %s AND cnrfc.date_created < %s "
                                     "GROUP BY cnrfc.date_valid ORDER BY cnrfc.date_valid")
                                     .format((cnrfc_meter), (cnrfc_meter), (pcwa_meter)),
                                     [user_selected_start, user_selected_end])

    def pcwa_metered(self, station_id, user_selected_start):
        return Forecasts.objects.raw("SELECT 1 as id, * "
                                     "FROM metered_actuals "
                                     "WHERE date_valid > %s ",
                                     [user_selected_start])

    def analog_finder(self, pcwa_meter, cnrfc_meter, user_selected_start, user_selected_end):
        return Forecasts.objects.raw((
            "SELECT 1 as id, cnrfc.{} * 1000 as {}, metered.{}, cnrfc.date_valid as cnrfc_date, "
            "metered.date_valid, ROUND((cnrfc.MFAC1*1000)-metered.R11) as R11_error, a.precip, "
            "(SELECT MIN(a.ROWID) FROM actuals AS aa WHERE aa.ROWID > a.ROWID) as next_rowid, "
            "(SELECT precip from actuals as precip where precip.ROWID = "
            "(SELECT MIN (aa.ROWID) FROM actuals as aa WHERE aa.ROWID > a.ROWID)) as next_actual, "
            "(SELECT CASE WHEN "
            "(SELECT precip from actuals as precip WHERE precip.ROWID = "
                  "(SELECT MIN (aa.ROWID) FROM actuals as aa WHERE aa.ROWID > a.ROWID)) - a.precip > 0 "
            "THEN "
            "ROUND((SELECT precip from actuals as precip WHERE precip.ROWID = "
                  "(SELECT MIN (aa.ROWID) FROM actuals as aa WHERE aa.ROWID > a.ROWID)) - a.precip,2) "
            "ELSE 0 "
            "END) AS precip_hr "
            "FROM cnrfc_actuals as cnrfc "
            "JOIN metered_actuals AS metered ON DATETIME(cnrfc.date_valid,'localtime')=metered.date_valid "
            "JOIN actuals as a on DATETIME(cnrfc.date_valid,'localtime')=a.date_valid "
            "WHERE cnrfc.date_created > %s AND cnrfc.date_created < %s "
            "GROUP BY cnrfc.date_valid ORDER BY cnrfc.date_valid ")
             .format((cnrfc_meter), (cnrfc_meter), (pcwa_meter)),[user_selected_start, user_selected_end])

class Forecasts(models.Model):
    date_created = models.TextField()
    date_valid = models.DateTimeField()
    station_id = models.TextField()
    objects = Historical()

    def __unicode__(self):
        return u'%s %s %s %s' % (self.date_created, self.date_valid, self.station_id)

    class Meta:
        # Django automatically derives the table name from the database class name and the
        # app that contains it (e.g. "weatherapp" "Forecasts" in this case). The database table will have the name
        # of the app + the name of the Class with an underscore between them (e.g. weatherapp_Forecast in this case).
        # To override the database table name, use the db_table parameter in class Meta (as shown below).
        db_table = 'cnrfc_fcst'

class DateRange(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    # start_time = models.TimeField()
    # end_time = models.TimeField()
    def __unicode__(self):
        return u'%s %s %s %s' % (self.name, self.start_date, self.end_date)

