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

        self.report.indicators.add(self.height_indicator)
        
        self.record = Record.objects.get_or_create(report=self.report)
        self.record.eav.height = 10
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
    
        report_view = ReportView.objects.get_or_create(report=self.report)[0]
        report_view.indicators.add(self.height_indicator)
        
        self.assertEqual(report_view.get_labels(), ['Height'])
        self.assertEqual(report_view.get_data_matrice(), [{'Height': 10}])
        
    
    def test_create_view_from_report(self):
        pass
        
        
    def test_create_from_attribute_with_params(self):
        pass  
