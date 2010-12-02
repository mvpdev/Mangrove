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
            body.append([indic.value(record) for indic in indicators])
            
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
    """
        A type of value for the report. A report will have several indicator,
        which it will use to choose what kind of data to display.
        
        It extracts the corresponding
        value from each record, wether directly or by calculating it.
        
        The way to calculate the value depends of the indicator type.
        
    """

    class Meta:
        verbose_name = __('indicator')


    TYPE_CHOICES = (('value', __('Value')), 
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
                                    
                                    
    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.strategy = dict(self.__class__.STRATEGY_CHOICES)[self.type]
 

    def __save__(self, *args, **kwargs):
        # you should not be able to change the type or the contept
        # after creating the indicator
        try:
            old_self = Indicator.objects.get(pk=self.pk)
            
            if self.concept != old_self.concept:
                raise IntegrityError(_("The concept can not be changed anymore"))
                
            if self.type != old_self.type:
                raise IntegrityError(_("The type can not be changed anymore"))
        except Indicator.DoesNotExist:
            pass
        models.Model.__save__(self, *args, **kwargs)
        
        
    def value(self, record):
        """
            Return the value of this indicator for this record, using the
            proper behavior according to the indicator type.
        """
        return self.strategy.value(self, record)
    
    
    def __unicode__(self):
        return self.name


class ValueIndicator(Indicator):

    class Meta:
        proxy = True
        
    @staticmethod
    def value(instance, record):
        """
            Return directly the value of this indicator in this record.
        """
        return getattr(record.eav, instance.concept.slug, None)

# todo: add checks on indicator parameters type (can't sum a district)

class RatioIndicator(Indicator):     

    class Meta:
        proxy = True   
        
    # todo: add checks for ratio to accept 2 and only two args
    @staticmethod
    def value(instance, record):
        """
            Return a ratio between the values of the 2 indicators in this
            record.
        """
        ind_1, ind_2 = instance.params.all()
        return round(operator.truediv(ind_1.value(record), 
                                      ind_2.value(record)), 2)



class RateIndicator(Indicator): 

    class Meta:
        proxy = True 
        
    # todo: add checks for rate to accept 2 and only two args
    @staticmethod
    def value(instance, record):
        """
            Return a rate between the values of the 2 indicators in this
            record.
        """
        ind_1, ind_2 = instance.params.all()
        ratio = operator.truediv(ind_1.value(record), 
                                 ind_2.value(record)) * 100
        return round(ratio, 2)


class AverageIndicator(Indicator): 

    class Meta:
        proxy = True 
        
    @staticmethod
    def value(instance, record):
        """
            Return the average of the values for these indicators in this
            record.
        """
        values = [ind.value(record) for ind in instance.params.all()]
        return round(operator.truediv(sum(values), len(values)), 2)  


class SumIndicator(Indicator): 

    class Meta:
        proxy = True 
        
    @staticmethod
    def value(instance, record):
        """
            Return the sum of the values for these indicators in this
            record.
        """
        return sum(ind.value(record) for ind in instance.params.all())


class ProductIndicator(Indicator): 

    class Meta:
        proxy = True 
        
    @staticmethod
    def value(instance, record):
        """
            Return the product of the values for these indicators in this
            record.
        """
        return reduce(operator.mul, 
                     (ind.value(record) for ind in instance.params.all()))


class DifferenceIndicator(Indicator): 

    class Meta:
        proxy = True 
        
    @staticmethod
    def value(instance, record):
        """
            Return the difference of the values for these indicators in this
            record.
        """
        return reduce(operator.sub, 
                     (ind.value(record) for ind in instance.params.all()))
    
# Mappting between indicator types and calculated indicator algo
# we can't make that in the class definition as the following classes are not
# defined yet but be can't put indicator here since they inherit from it
Indicator.STRATEGY_CHOICES = (('value', ValueIndicator), 
                        ('ratio',  RatioIndicator),
                        ('average', AverageIndicator),
                        ('sum', SumIndicator),
                        ('product', ProductIndicator),
                        ('difference', DifferenceIndicator),)    
