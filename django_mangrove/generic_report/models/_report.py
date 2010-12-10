#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
import eav

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models
from django.utils.datastructures import SortedDict
from django.db.models.signals import m2m_changed

from code_generator.fields import CodeField

"""
    Reports (a group of data), report views (the way to display the data) and
    records (a batch of raw data). You may want to start with reports if 
    you are new to the code.
"""

# todo: remove start date and end dates and code and frenquency
# todo: add constraint to a report
class Report(models.Model):
    """
        Central object for this app, it is the link between all other 
        components. A report declare several indicators (see indicator.py) 
        and contains several data records. Views tell how to display 
        these records.
    """

    class Meta:
        verbose_name = __('report')
        app_label = 'generic_report'
        

    name = models.CharField(max_length=64, verbose_name=__(u'name'))

    def __unicode__(self):
        return _(u'%(name)s') % {'name': self.name}



# todo: check that indicators are only from the report indicator
# todo: add indicator orders
class ReportView(models.Model):
    """
        A way to display the data of the report. Declare:
        
        - pagination (see paginator.py), meaning wich 
          portion of data you want to see. E.G: by batch of 10 records.
        - filtering (see filter.py), meaning which type of data you want to see.
          E.G: only data with value X < 45.
        - aggregation (see agregator.py), meaning how grouped you want the 
          data to be. E.G: grouped by date.
        - ordering (see orderer.py), meaning in which order you the data to
          appear. E.G: in alphabetical order.
    """

    class Meta:
        verbose_name = __('report view')
        verbose_name_plural = __('report views')
        unique_together = (('report', 'name'),)
        app_label = 'generic_report'
        

    report = models.ForeignKey(Report, related_name='views') 
    name = models.CharField(max_length=64, 
                            verbose_name=__(u'name'),
                            default=__('default'))
    time_format = models.CharField(max_length=32, 
                                   verbose_name=__(u'time format'),
                                   default='%m/%d/%y')  


    def get_selected_indicators(self):
        sis = self.selected_indicators.all().order_by('order')
        indicators = [si.indicator for si in sis]
        
        # if there is an aggregation, remove non numeric indicators
        if self.aggregators.all().exists():
            aggregator = self.aggregators.all()[0]
            t_int = eav.models.Attribute.TYPE_INT
            filtered_indicators = []
            for indicator in indicators:
                if indicator.concept.datatype == t_int \
                   or indicator.concept == aggregator.indicator.concept:
                   filtered_indicators.append(indicator)
            return filtered_indicators
        return indicators


    def get_labels(self):
        return [si.name for si in self.get_selected_indicators()]
      

    # cache that
    def get_data_matrice(self):
    
        matrice = []
        records = self.report.records.all()
        sis = self.selected_indicators.all().order_by('order')
        indicators = self.get_selected_indicators()
        
        # first, extract data from record as a dict
        matrice = [record.to_sorted_dict(indicators) for record in records]
         
        # todo: optimize extraction / calculation by separating indicator
        # for both process and avoiding extracting value indicators twice
        # secondly,calculate the data 
        
        for record in matrice:
            for indic in indicators:
                record[indic.concept.slug] = indic.value(self, record) 

        # thirdly aggregate / filter the data
        for aggregator in self.aggregators.all():
            matrice = aggregator.get_aggregated_data(matrice)
       
        # enventually, format the data 
        for record in matrice:
            for indic in indicators:
                record[indic.concept.slug] = indic.format(self, record)
            
        return matrice
            
        
    def get_extracted_data(self):
        return []
       
       
    @classmethod
    def create_from_report(cls, report, name='Default'):
        """
            Create a view fromt the given report. The view will be attached
            to this report and reference the same indicators.
        """
        
        view = ReportView.objects.create(report=report, name=name)
        for ind in report.indicators.all():
            view.add_indicator(ind)
        return view
  
  
    # todo: create similar method for removing indicators
    # todo: check if indicators belong to the report first
    def add_indicator(self, indicator, order=None):
        """
            Add an indicator to the current view. if it doesn't exists in 
            the associated report, add it to it too.
            Returns the ViewIndactor object responsible for the relation
            between the indicator and the view.
        """
        vi = SelectedIndicator.objects.create(view=self, indicator=indicator, 
                                          order=order)
       
        if indicator not in self.report.indicators.all():
            self.report.indicators.add(indicator)
        
        return vi
        
        
    def __unicode__(self):
        return _('View "%(view)s" of report "%(report)s"') % {
                 'view': self.name, 'report': self.report}

# todo: remove date and set that as an indicator automatically created
class Record(models.Model):
    """
        A batch of raw data. A record hold data using the django-eav app. 
        The app never access the report directly, each piece of data is 
        extracted from the record using an indicator objects (see indicator.py).
    """


    class Meta:
        verbose_name = __('record')
        verbose_name_plural = __('records')
        app_label = 'generic_report'


    date = models.DateField(default=datetime.datetime.today,
                                  verbose_name=__(u'date'))
    validated = models.BooleanField(default=False)
    report =  models.ForeignKey(Report, related_name='records') 
    
    def __unicode__(self):
        return _("Record %(record)s (sent on %(date)s) of report %(report)s") % {
                 'record': self.pk, 'report': self.report, 'date': self.date}

    def to_sorted_dict(self, indicators):
        data = SortedDict()
        for indicator in indicators:
            try:
                attr = indicator.concept.slug
                data[attr] = getattr(self.eav, attr)
            except AttributeError:
                pass
        return data


