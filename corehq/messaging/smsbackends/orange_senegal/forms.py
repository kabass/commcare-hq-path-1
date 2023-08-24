from corehq.apps.sms.forms import BackendForm, LoadBalancingBackendFormMixin
from dimagi.utils.django.fields import TrimmedCharField
from crispy_forms import layout as crispy
from django.utils.translation import gettext_lazy as _


class OrangeSNBackendForm(BackendForm):
    basic_auth = TrimmedCharField(
        label=_("Basic Auth"),
    )
    from_phone_number = TrimmedCharField(
        label=_("From Phone number"),
    )

    @property
    def gateway_specific_fields(self):
        return crispy.Fieldset(
            _("Orange Senegal Settings"),
            'basic_auth',
            'from_phone_number',
        )

    def validate_phone_number(self, phone_number: str) -> None:
        from corehq.messaging.smsbackends.orange_senegal.models import SQLOrangeSNBackend
        if not SQLOrangeSNBackend.phone_number_is_messaging_service_sid(phone_number):
            super().validate_phone_number(phone_number)
