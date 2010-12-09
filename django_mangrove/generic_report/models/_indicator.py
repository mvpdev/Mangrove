#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    List of classes used to define data types that composed a report.
    Indicator is the base class that uses all other indicator classes to 
    perform its job.
    One exception is Selected indicator, which is just a bridge between 
    indicators and report views.
"""

import eav.models
import operator

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models


# todo: refactor selected_indictor to use the through param
class SelectedIndicator(models.Model):
    """
        Holder relationship between ReportView and Indicator.
        Used to be able to specify an order in indicators for views.
    """
    
    class Meta:
        app_label = 'generic_report'
        unique_together = (('view','indicator','order'),)

    view = models.ForeignKey('generic_report.ReportView', related_name='selected_indicators')
    indicator = models.ForeignKey('Indicator', related_name='selected_for')
    order = models.IntegerField()
    
    def save(self, *args, **kwargs):
        
        # by default, create and order by incrementing the previous one,
        # or by setting it to 1 if no previous indicator exists for this view
        if not self.order:
            try:
                siblings = SelectedIndicator.objects.filter(view=self.view)
                self.order = siblings.latest('order').order  + 1
            except SelectedIndicator.DoesNotExist:
                self.order = 1
        
        models.Model.save(self, *args, **kwargs)

    def __unicode__(self):
        return "Selected indicator %(order)s for '%(view)s': %(indicator)s" % {
                'order': self.order, 'view': self.view, 
                'indicator': self.indicator}


# todo: make Parameter an intermediate models for m2m
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
        Each indicator type match a class wich contains the algo to extract
        the values. All these classes are in the '_indicator.py' file.
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

    report = models.ManyToManyField('generic_report.Report', 
                                    verbose_name=__(u'report'),
                                    related_name='indicators', 
                                    blank=True, null=True, symmetrical=False)
                                    
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
    
    
    @classmethod
    def create_from_attribute(cls, attr, indicator_type='value', params=()):
        """
            Create an indicator from the given EAV attribute. The indicator
            will be linked to this indicator and have the same name.
            
            By default, the indicator is a 'value' indicator. Pass type and
            a list of indicators as params to choose a different indicator type.
            Parameter order will be the same as the order of items in 'params'.
        """
        ind = Indicator.objects.create(type=indicator_type, concept=attr, 
                                       name=attr.name)
        for order, indicator in enumerate(params):
            ind.add_param(indicator, order)
        return ind   


    @classmethod
    def create_with_attribute(cls, name, attr_type=eav.models.Attribute.TYPE_INT, 
                              indicator_type='value', params=()):
        """
            Create an indicator and the related EAV attribute. The indicator
            will be linked to this indicator wich will have the same name.
            
            This first attempts to create the attribute (to let the creation
            fail if it needs to) then it calls 'create_from_attribute' on it.
        """
        
        attr, created = eav.models.Attribute.objects.get_or_create(name=name, 
                                                          datatype=attr_type)
        return cls.create_from_attribute(attr, indicator_type, params)
    
    
    def add_param(self, indicator, order=None):
        """
            Add the given indicator as a parameter of the current one. If no
            order is provided, the order will be calculated by taking the 
            highest parameter order for all params of this indicators and 
            adding 1.
        """
        # todo : move the param order check in param
        if not order:
            try:
                order = self.params.latest('order').order  + 1
            except Parameter.DoesNotExist:
                order = 1
        
        Parameter.objects.create(param_of=self, indicator=indicator, 
                                 order=order)
    
    
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
