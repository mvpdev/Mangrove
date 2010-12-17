from datetime import datetime

from django.test import TestCase

from generic_report.models import *
from generic_report_admin.forms import *
from eav.models import *

eav.register(Record)

class FormsTests(TestCase):

    """
        Testing report basics such as reports creation, views, indicators, etc.
    """


    def setUp(self):
        self.report = Report.objects.create(name='Square')
        self.height = Attribute.objects.create(name='Height', 
                                               datatype=Attribute.TYPE_INT)
        self.height_indicator = Indicator.create_from_attribute(self.height)

        self.width = Attribute.objects.create(name='Width', 
                                               datatype=Attribute.TYPE_INT)
        self.width_indicator = Indicator.create_from_attribute(self.width)

        self.report.indicators.add(self.height_indicator)
        self.report.indicators.add(self.width_indicator)
        
        self.view = ReportView.create_from_report(report=self.report, 
                                                  name='main')
        
        self.record = Record.objects.create(report=self.report)
        self.record.eav.height = 10
        self.record.eav.width = 2
        self.record.save()
        
        

    def test_form_creation(self):
        rf = RecordForm(report=self.report)
        
        self.assertEqual(rf.__class__.__name__, 'SquareRecordForm')
        self.assertEqual(sorted(rf.base_fields.keys()), ['height', 'width'])
 
 
    def test_basic_validation(self):
        rf = RecordForm({'width':5, 'height':3}, report=self.report)
        self.assertTrue(rf.is_valid())
        rf = RecordForm({'width':5,}, report=self.report)
        self.assertFalse(rf.is_valid())
        
        
    def test_saving_record_form_create_a_record(self):
        self.assertEqual(self.report.records.count(), 1)
        
        rf = RecordForm({'width':5, 'height':3}, report=self.report)
        rf.is_valid()
        record = rf.save()
        
        self.assertEqual(self.report.records.count(), 2)
        self.assertEqual(record.eav.height, 3)
        self.assertEqual(record.eav.width, 5)
