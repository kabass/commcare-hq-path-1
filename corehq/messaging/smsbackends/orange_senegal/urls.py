from django.conf.urls import re_path as url
from corehq.messaging.smsbackends.orange_senegal.views import (OrangeSNIncomingSMSView,
    OrangeSNIncomingIVRView)


urlpatterns = [
    url(r'^sms/(?P<api_key>[\w-]+)/?$', OrangeSNIncomingSMSView.as_view(),
        name=OrangeSNIncomingSMSView.urlname),
    url(r'^ivr/(?P<api_key>[\w-]+)/?$', OrangeSNIncomingIVRView.as_view(),
        name=OrangeSNIncomingIVRView.urlname),
]
