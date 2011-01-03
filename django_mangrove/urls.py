#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import login , logout_then_login

admin.autodiscover()

import os

urlpatterns = patterns('',

    # admin
    (r'^admin/', include(admin.site.urls)),

    # rapidsms
    (r'^', include('rapidsms.urls.login_logout')),
    (r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    (r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    (r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('logger_ng.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    (r'^registration/', include('rapidsms.contrib.auth.urls')),
    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),

    url(r'^rapidsms-dashboard/$',
        'rapidsms.views.dashboard',
        name='rapidsms-dashboard'),

    (r'^', include('rapidsms_xforms.urls')),

)

if settings.DEBUG:

    urlpatterns += patterns("", 

        url("%s/common/(?P<path>.*)$" % settings.MEDIA_URL.strip('/'),
            "django.views.static.serve",
            {"document_root": os.path.join(settings.PROJECT_DIR, 'static'),
              'show_indexes': True}
            ),
 
        url("%s/mangrove_demo/(?P<path>.*)$" % settings.MEDIA_URL.strip('/'),
            "django.views.static.serve",
            {"document_root":
              os.path.join(settings.PROJECT_DIR, 'mangrove_demo', 'static'),
              'show_indexes': True}
            ),

        url(r'^', include('rapidsms.urls.static_media')),
    )


urlpatterns += patterns("",
    
    url(r'^login/$', login, name='ntd-login', 
        kwargs={"template_name" : 'login.html'}),
    url(r'^logout/$', logout_then_login, name='ntd-logout'),
    url(r'^', include('mangrove_demo.urls'), name='mangrove-dashboard'),    
    
)



