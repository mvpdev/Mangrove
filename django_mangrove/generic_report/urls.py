#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import redirect_to

from .models import Report

urlpatterns = patterns("",

    # todo: change that
    url(r'reports/manage/$', object_list, {'queryset': Report.objects.all(),
                                       'template_name': 'campaigns-list.html', 
                                       'template_object_name': 'campaigns'}, 
        name="reports-list"),

    url(r'switch-language/$',  "generic_report.views.switch_lang", name='switch-lang'), 
    
    url(r'report/(?P<id>\d+)/results/$',  
        "generic_report.views.report_results", name='report-results'), 
    
    url(r'$',  redirect_to, { 'url': "/reports/manage/" }, name='dashboard')
)


