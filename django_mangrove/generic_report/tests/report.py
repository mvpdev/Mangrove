from datetime import datetime

from django.test import TestCase

from ..models import *
from eav.models import *

eav.register(Record)

class ReportTests(TestCase):

    """
        Testing report basics such as reports creation, views, indicators, etc.
    """


    def setUp(self):
        self.report = Report.objects.get_or_create(name='Square')[0]
        self.height = Attribute.objects.get_or_create(name='Height', 
                                               datatype=Attribute.TYPE_INT)[0]
        self.height_indicator = Indicator.create_from_attribute(self.height)

        self.width = Attribute.objects.get_or_create(name='Width', 
                                               datatype=Attribute.TYPE_INT)[0]
        self.width_indicator = Indicator.create_from_attribute(self.width)

        self.report.indicators.add(self.height_indicator)
        self.report.indicators.add(self.width_indicator)
        
        self.view = ReportView.create_from_report(report=self.report, 
                                                  name='main')
        
        self.record = Record.objects.get_or_create(report=self.report)
        self.record.eav.height = 10
        self.record.eav.width = 2
        self.record.save()
        

    def tearDown(self):
        pass


    def test_basic_report_with_one_indicator(self):
        r = Report.objects.create(name='Test')
        a = Attribute.objects.get_or_create(name='Height', 
                                            datatype=Attribute.TYPE_INT)[0]
        i = Indicator.objects.get_or_create(name='i_test', concept=a, 
                                             type='value')[0]
        r.indicators.add(i)

        self.assertEqual(r.indicators.count(), 1)
        self.assertEqual(r.indicators.all()[0].name, 'i_test')
        self.assertEqual(r.indicators.all()[0].concept, a)
        
        record = Record.objects.get_or_create(report=r)
        record.eav.height = 10
        record.save()
        
        self.assertEqual(r.records.count(), 1)
        self.assertEqual(r.records.all()[0], record)
        self.assertEqual(r.records.all()[0].eav.height, 10)


    def test_create_basic_indicator_from_attribute(self):
        r = Report.objects.get_or_create(name='Test')[0]
        a = Attribute.objects.get_or_create(name='Age', 
                                            datatype=Attribute.TYPE_INT)[0]
        i = Indicator.create_from_attribute(a)
        r.indicators.add(i)

        self.assertEqual(r.indicators.count(), 1)
        self.assertEqual(r.indicators.all()[0].name, 'Age')
        self.assertEqual(r.indicators.all()[0].type, 'value')
        self.assertEqual(r.indicators.all()[0].concept, a)


    def test_get_data_matrice_from_report(self):
    
        report_view = ReportView.objects.create(report=self.report)
        report_view.indicators.add(self.height_indicator)
        
        self.assertEqual(report_view.get_labels(), ['Height'])
        self.assertEqual(report_view.get_data_matrice(), [{'Height': 10}])
        
    
    def test_create_view_from_report(self):
        report_view = ReportView.create_from_report(report=self.report)
        
        self.assertEqual(report_view.get_labels(), ['Height', 'Width'])
        self.assertEqual(report_view.get_data_matrice(), [{'Height': 10,
                                                           'Width': 2}])
        
   
    def test_create_indictor_with_attribute(self):
        ind = Indicator.create_with_attribute('Time')
        
        self.assertEqual(ind.name, 'Time')
        self.assertEqual(ind.concept.name, 'Time')   
        self.assertEqual(ind.concept.datatype, Attribute.TYPE_INT)   
 
 
    def test_calculated_indicator(self):
        
        area = Attribute.objects.get_or_create(name='Area', 
                                               datatype=Attribute.TYPE_INT)[0]
        i = Indicator.objects.create(type='product', concept=area, name='Area')
        self.report.indicators.add(i)
        self.view.indicators.add(i)
        
        Parameter.objects.create(param_of=i, order=1, 
                                 indicator=self.height_indicator)
                                 
        Parameter.objects.create(param_of=i, order=2, 
                                 indicator=self.width_indicator)
        
        self.assertEqual(self.view.get_labels(), ['Height', 'Width', 'Area'])
        self.assertEqual(self.view.get_data_matrice(), [{'Height': 10, 
                                                           'Width': 2, 
                                                           'Area': 20, }]) 
       
        
    def test_create_indic_from_attribute_with_params(self):
        area = Attribute.objects.get_or_create(name='Area', 
                                               datatype=Attribute.TYPE_INT)[0]
        i = Indicator.create_from_attribute(area, 'product',
                                            (self.height_indicator, 
                                             self.width_indicator))

        self.report.indicators.add(i)
        self.view.indicators.add(i)

        self.assertEqual(self.view.get_labels(), ['Height', 'Width', 'Area'])
        self.assertEqual(self.view.get_data_matrice(), [{'Height': 10, 
                                                           'Width': 2, 
                                                           'Area': 20, }]) 

        
    def test_create_indic_with_attribute_with_params(self):
  
        i = Indicator.create_with_attribute('Area', Attribute.TYPE_INT, 
                                            'product', (self.height_indicator, 
                                                        self.width_indicator))

        self.report.indicators.add(i)
        self.view.indicators.add(i)

        self.assertEqual(self.view.get_labels(), ['Height', 'Width', 'Area'])
        self.assertEqual(self.view.get_data_matrice(), [{'Height': 10, 
                                                           'Width': 2, 
                                                           'Area': 20, }]) 

        
    def test_add_param(self):
                   
        area = Attribute.objects.get_or_create(name='Area', 
                                               datatype=Attribute.TYPE_INT)[0]
        i = Indicator.objects.create(type='product', concept=area, name='Area')
        
        i.add_param(self.height_indicator, 2)
        i.add_param(self.width_indicator)
        
        self.report.indicators.add(i)
        self.view.indicators.add(i)
        
        params = i.params.all()
        
        self.assertEqual(params.count(), 2)
        self.assertEqual(params[0].order, 2)
        self.assertEqual(params[1].order, 3)
        
        self.assertEqual(self.view.get_labels(), ['Height', 'Width', 'Area'])
        self.assertEqual(self.view.get_data_matrice(), [{'Height': 10, 
                                                           'Width': 2, 
                                                           'Area': 20, }]) 
        
    def test_add_an_indicator_to_a_view_add_it_to_its_report(self):
        i = Indicator.create_with_attribute('Area', Attribute.TYPE_INT, 
                                            'product', (self.height_indicator, 
                                                        self.width_indicator))

        self.view.indicators.add(i)
        
        self.assertTrue(i in self.report.indicators.all())

        
    def test_calculated_indicator_with_calculated_indicator_as_param(self):
        i1 = Indicator.create_with_attribute('Area', Attribute.TYPE_INT, 
                                            'product', (self.height_indicator, 
                                                        self.width_indicator))
                                                        
        self.view.indicators.add(i1)

        i2 = Indicator.create_with_attribute('Average', Attribute.TYPE_INT, 
                                            'ratio', (self.height_indicator, 
                                                      i1))
        self.view.indicators.add(i2)
        
        self.assertEqual(self.view.get_labels(), ['Height', 'Width', 
                                                  'Area', 'Average'])
        self.assertEqual(self.view.get_data_matrice(), [{'Height': 10, 
                                                           'Width': 2, 
                                                           'Area': 20, 
                                                           'Average': 0.5}]) 
