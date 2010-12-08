#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4


from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import check_for_language
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from .models import Report, ReportView


@login_required
def report_results(request, id):

    report = Report.objects.get(pk=id)
    report_views = report.views.all().order_by('pk')
    
    if report_views:
    
        paginator = Paginator(report_views, 1) # Show 1 view per page

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last view.
        try:
            page = paginator.page(page)
        except (EmptyPage, InvalidPage):
            page = paginator.page(page.num_pages)

        view = page.object_list[0]

        header = view.get_labels()
        body = view.get_data_matrice()
        
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



