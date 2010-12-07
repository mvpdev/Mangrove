#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4

"""
    Classes that labels values from records and group data according to this
    labels, summing numerical data and hidding non numerical data.
    Act like an SQL 'GROUP BY' but for data matrices generated from reports.
"""

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models


class Aggregator(models.Model):
    pass
