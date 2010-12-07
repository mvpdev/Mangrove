#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
import operator
import eav.models

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models

from code_generator.fields import CodeField


"""
    Reports (a group of data), report views (the way to display the data) and
    records (a batch of raw data). You may want to start with reports if 
    you are new to the code.
"""


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

    def __unicode__(self):
        return _(u'%(name)s (starts on %(date)s)') % {'name': self.name,
               'date': self.start_date.strftime(_('%m/%d/%Y'))}


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
        

    report = report =  models.ForeignKey(Report, related_name='views') 
    name = models.CharField(max_length=64, 
                            verbose_name=__(u'name'),
                            default=__('default'))
    indicators = models.ManyToManyField('Indicator', 
                                        verbose_name=__(u'indicators'),
                                        related_name='views', 
                                        blank=True, null=True,
                                        symmetrical=False)


    def get_header(self):
        return [indic.name for indic in self.indicators.all()]
      
        
    # cache that
    def get_body(self, start_date, end_date):
        body = []
        records = self.report.records.all().filter(date__gte=start_date, 
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
        return _('View "%(view)s" of report "%(report)s"') % {
                 'view': self.name, 'report': self.report}


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


class Parameter(models.Model):
    """
        Link between a calculated indicator and it's parameter.
        Gives an order.
    """
    
    class Meta:
        unique_together = (('param_of', 'indicator', 'order'))
        app_label = 'generic_report'
        
    
    param_of = models.ForeignKey('Indicator', related_name='params') 
    indicator = models.ForeignKey('Indicator', related_name='as_params') 
    order = models.IntegerField()
    
    def __unicode__(self):
        return "Param %s of %s" % (self.order, self.param_of)


# todo: add checks for parameter number
# todo: add checks for calculation dependancies
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
        app_label = 'generic_report'


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
                                    
    type = models.CharField(max_length=64, verbose_name=__(u'type'),
                            choices=TYPE_CHOICES)
                                    
                                    
    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        
        if self.type:
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
        
        if not self.strategy:
            raise ValueError('Can not get value with an unsaved indicator')
        
        return self.strategy.value(self, record)
    
    
    def __unicode__(self):
        return self.name



class ValueIndicator(Indicator):

    class Meta:
        proxy = True
        app_label = 'generic_report'
        
        
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
        app_label = 'generic_report'
        
        
    # todo: add checks for ratio to accept 2 and only two args
    @staticmethod
    def value(instance, record):
        """
            Return a ratio between the values of the 2 indicators in this
            record.
        """
        param_1, param_2 = instance.params.all().order_by('order')
        return round(operator.truediv(param_1.indicator.value(record), 
                                      param_2.indicator.value(record)), 2)



class RateIndicator(Indicator): 

    class Meta:
        proxy = True 
        app_label = 'generic_report'
        
        
    # todo: add checks for rate to accept 2 and only two args
    @staticmethod
    def value(instance, record):
        """
            Return a rate between the values of the 2 indicators in this
            record.
        """
        param_1, param_2 = instance.params.all().order_by('order')
        ratio = operator.truediv(param_1.indicator.value(record), 
                                 param_2.indicator.value(record)) * 100
        return round(ratio, 2)



class AverageIndicator(Indicator): 

    class Meta:
        proxy = True 
        app_label = 'generic_report'
        
        
    @staticmethod
    def value(instance, record):
        """
            Return the average of the values for these indicators in this
            record.
        """
        parameters = instance.params.all().order_by('order')
        values = [param.indicator.value(record) for param in parameters]
        return round(operator.truediv(sum(values), len(values)), 2)  



class SumIndicator(Indicator): 

    class Meta:
        proxy = True 
        app_label = 'generic_report'
        
        
    @staticmethod
    def value(instance, record):
        """
            Return the sum of the values for these indicators in this
            record.
        """
        parameters = instance.params.all().order_by('order')
        return sum(param.indicator.value(record) for param in parameters)



class ProductIndicator(Indicator): 

    class Meta:
        proxy = True 
        app_label = 'generic_report'
        
        
    @staticmethod
    def value(instance, record):
        """
            Return the product of the values for these indicators in this
            record.
        """
        parameters = instance.params.all().order_by('order')
        return reduce(operator.mul, 
                     (param.indicator.value(record) for param in parameters))



class DifferenceIndicator(Indicator): 

    class Meta:
        proxy = True 
        app_label = 'generic_report'
        
        
    @staticmethod
    def value(instance, record):
        """
            Return the difference of the values for these indicators in this
            record.
        """
        parameters = instance.params.all().order_by('order')
        return reduce(operator.sub, 
                     (param.indicator.value(record) for param in parameters))
    
    
    
# Mappting between indicator types and calculated indicator algo
# we can't make that in the class definition as the following classes are not
# defined yet but be can't put indicator here since they inherit from it
Indicator.STRATEGY_CHOICES = (('value', ValueIndicator), 
                                ('ratio',  RatioIndicator),
                                ('average', AverageIndicator),
                                ('sum', SumIndicator),
                                ('product', ProductIndicator),
                                ('difference', DifferenceIndicator),
                                ('rate', RateIndicator))   
