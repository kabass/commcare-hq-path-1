from django.conf.urls import re_path as url
from corehq.messaging.smsbackends.twilio.views import (SimpleTwilioIncomingSMSView,
    SimpleTwilioIncomingIVRView)


urlpatterns = [
    url(r'^sms/(?P<api_key>[\w-]+)/?$', SimpleTwilioIncomingSMSView.as_view(),
        name=SimpleTwilioIncomingSMSView.urlname),
    url(r'^ivr/(?P<api_key>[\w-]+)/?$', SimpleTwilioIncomingIVRView.as_view(),
        name=SimpleTwilioIncomingIVRView.urlname),
]
