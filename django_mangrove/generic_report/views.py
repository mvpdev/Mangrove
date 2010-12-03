#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Sum
from django.conf import settings
from django.utils.translation import check_for_language


from .models import Report

from simple_locations.models import Area, AreaType




@login_required
def report_results(request, id):

    try:
        year = int(request.GET.get('year', 2010))
    except ValueError:
        year = 2010
        
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 0, 0)

    report = Report.objects.get(pk=id)
    default_view = report.views.all()[0]

    header = default_view.get_header()
    body = default_view.get_body(start_date, end_date)
        
    ctx = locals()

    return render_to_response('campaigns_results.html',  ctx,
                              context_instance=RequestContext(request))




     # todo: use the django view for this
def switch_lang(request):

    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'

    response = HttpResponseRedirect(next)
    if request.method == 'GET':
        lang_code = request.GET.get('lang_code', None)
        if lang_code and check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response



