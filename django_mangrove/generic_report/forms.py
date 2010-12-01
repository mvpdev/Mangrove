#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django import forms

from .models import Campaign
from django.forms import ValidationError
from django.utils.translation import ugettext as _

from simple_locations.models import Area

from report_parts.models import Report, ReportType

from .models import Results

# if we change the distributor, it should be set for all the active campagn

class CampaignForm(forms.ModelForm):

    class Meta:
        model = Campaign
        
        
    def clean(self, *args, **kwargs):
    
        if 'locations' not in self.data:
            raise ValidationError(_(u'You must select at least one location'))
        return forms.ModelForm.clean(self, *args, **kwargs)
            
            
    def save(self, *args, **kwargs):
        
        campaign = forms.ModelForm.save(self, *args, **kwargs)
    
        # todo : make add a slug to report type
        rt = ReportType.objects.get(name='NTD Mali')
        # todo: put more validation here
        # create or enable checked location
        locations = set(self.data.getlist('locations'))
        for location in locations:
            area = Area.objects.get(pk=location)
            
            try:
                result = Results.objects.get(campaign=campaign, area=area)
                if campaign.drugs_pack and not result.drugs_pack :
                    result.drugs_pack = campaign.drugs_pack
                    result.save()
            except Results.DoesNotExist:
                loc = area.as_data_source.data_collection
                pack = campaign.drugs_pack
                report_mgr = Report.objects.create(type=rt)
                result = Results.objects.create(campaign=campaign,
                                                area=area,
                                                data_collection_location=loc,
                                                drugs_pack=pack,
                                                report_manager=report_mgr)
            else:
                if result.disabled:
                    result.disabled = False
                    result.save()
                
        # disable unchecked locations
        for result in campaign.results_set.all():
            if unicode(result.area.pk) not in locations:
                result.disabled = True
                result.save()
    
        return campaign
       
