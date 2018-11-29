from django.conf.urls import url
from django.contrib import admin
from verification.views import index
from verification.production import cnrfc_verification
from verification.production import verification_map
from . import views  # import "." means import from the current package.
from datetime import datetime

urlpatterns = [
    url('^$', views.index),
    url(r'^admin/', admin.site.urls),
    url(r'^performance/', cnrfc_verification.chart, {'user_selected_site':'R11',
                                                       'model':'PCWA',
                                                       'user_selected_start': '2017-01-01 00:00:00',
                                                        'user_selected_end': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                     }, name='chart'),
    url(r'^map/', verification_map.map, name='map'),
    url(r'^mapchart/', verification_map.map_plus_chart, {'user_selected_site':'R11',
                                                        'user_selected_start': '2018-01-01 00:00:00',
                                                        'user_selected_end': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                     }, name='map_plus_chart'),
]