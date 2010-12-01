#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
import re
import operator

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models
from django.db.models import Q
from django.db.models import permalink

import eav.models

from simple_locations.models import Area

from code_generator.fields import CodeField


class Report(models.Model):

    class Meta:
        verbose_name = __('report')
        
    FREQUENCY_CHOICES = (
                         #('weekly', __('Weekly')),
                         #('monthly', __('Monthly')),
                         #('quaterly', __('Quaterly')),
                         ('yearly', __('Yearly')),)

    name = models.CharField(max_length=64, verbose_name=__(u'name'))
    code = CodeField(verbose_name=__("code"), max_length=12, prefix='r')
    start_date = models.DateField(default=datetime.datetime.today,
                                  verbose_name=__(u'start date'))
    end_date = models.DateField(blank=True, null=True,
                                verbose_name=__(u'end date'))

    frequency = models.CharField(max_length=24, verbose_name=__(u'frequency'),
                                 choices=FREQUENCY_CHOICES)
                                
    def get_header(self):
        return [indic.name for indic in self.indicators.all()]
        
    # cache that
    def get_body(self, start_date, end_date):
        body = []
        records = self.record_set.all().filter(date__gte=start_date, 
                                           date__lte=end_date,)\
                                   .order_by('date')
        indicators = self.indicators.all()
        
        # todo: put than in an ordered dict
        for record in records:
            body.append(indic.get_value(record) for indic in indicators)
            
        return body
            
        
    def footer(self):
        return []

    def __unicode__(self):
        return _(u'%(name)s (starts on %(date)s)') % {'name': self.name,
               'date': self.start_date.strftime(_('%m/%d/%Y'))}



class Record(models.Model):

    date = models.DateField(default=datetime.datetime.today,
                                  verbose_name=__(u'date'))
    validated = models.BooleanField(default=False)
    report =  models.ForeignKey(Report) 
    
    def __unicode__(self):
        return "# %s" % self.pk


# todo: add checks for parameter number
# todo: add checks for calculation dependancies
# todo: refactor this as several classes ?
class Indicator(models.Model):

    class Meta:
        verbose_name = __('indicator')


    TYPE_CHOICES = (('value', __('value')), 
                    ('ratio', __('Ratio')),
                    ('average', __('Average')),
                    ('sum', __('Sum')),
                    ('product', __('Product')),
                    ('difference', __('Difference')),
                    ('rate', __('Rate')),)

    # make it default to concept name
    name = models.CharField(max_length=64, verbose_name=__(u'name'))
    
    # todo: this field need a descritpion for south to freeze it
    concept = models.ForeignKey(eav.models.Attribute)   

    report = models.ManyToManyField(Report, 
                                    verbose_name=__(u'report'),
                                    related_name='indicators', 
                                    blank=True, null=True)

    params = models.ManyToManyField('self', 
                                    verbose_name=__(u'parameters'),
                                    related_name='params_of', 
                                    blank=True, null=True, symmetrical=False)
                                    
    type = models.CharField(max_length=64, verbose_name=__(u'type'),
                            choices=TYPE_CHOICES)
                                    
    def get_value(self, record):
        
        return getattr(self, self.type)(record)
        
    def value(self, record):
        """
            Return directly the value of this indicator in this record.
        """
        print self, "value"
        return getattr(record.eav, self.concept.slug, None)
        
        
    # todo: add checks for ratio to accept 2 and only two args
    def ratio(self, record):
        """
            Return a ratio between the values of the 2 indicators in this
            record.
        """
        print self, "ratio"
        values = self.params.all()
        return round(operator.truediv(values[0].get_value(record),
                                values[1].get_value(record)), 2)


    # todo: add checks for rate to accept 2 and only two args
    def rate(self, record):
        """
            Return a rate between the values of the 2 indicators in this
            record.
        """
        values = self.params.all()
        ratio = operator.truediv(values[0].get_value(record),
                                values[1].get_value(record)) * 100
        return round(ratio, 2)


    def average(self, record):
        """
            Return the average of the values for these indicators in this
            record.
        """
        values = [param.get_value(record) for param in self.params.all()]
        return round(operator.truediv(sum(values), len(values)), 2)  


    def sum(self, record):
        """
            Return the sum of the values for these indicators in this
            record.
        """
        print self, "sum"
        return sum(param.get_value(record) for param in self.params.all())


    def product(self, record):
        """
            Return the product of the values for these indicators in this
            record.
        """
        return reduce(operator.mul, 
                     (param.get_value(record) for param in self.params.all()))


    def difference(self, record):
        """
            Return the difference of the values for these indicators in this
            record.
        """
        return reduce(operator.sub, 
                     (param.get_value(record) for param in self.params.all()))
    
    
    def __unicode__(self):
        return self.name


