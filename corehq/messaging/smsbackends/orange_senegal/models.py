from typing import Optional

import json
import requests


from django.utils.functional import classproperty

from dimagi.utils.logging import notify_exception

from corehq import toggles
from corehq.apps.domain.models import Domain
from corehq.apps.sms.models import SMS, SQLSMSBackend
from corehq.apps.sms.util import clean_phone_number
from corehq.apps.smsbillables.exceptions import RetryBillableTaskException
from corehq.messaging.smsbackends.orange_senegal.forms import OrangeSNBackendForm

# https://www.twilio.com/docs/api/errors/reference
INVALID_TO_PHONE_NUMBER_ERROR_CODE = 21211
WHATSAPP_LIMITATION_ERROR_CODE = 63032
TO_FROM_BLACKLIST_ERROR_CODE = 21610
REGION_PERMISSION_ERROR_CODE = 21408
MESSAGE_BODY_REQUIRED_ERROR_CODE = 21602

WHATSAPP_PREFIX = "whatsapp:"
WHATSAPP_SANDBOX_PHONE_NUMBER = "14155238886"


class SQLOrangeSNBackend(SQLSMSBackend):

    @classproperty
    def url(cls):
        # for SSL verification only
        # use classproperty to avoid evaluation on import
        return Api(None).base_url

    class Meta(object):
        app_label = 'sms'
        proxy = True

    using_api_to_get_fees = True

    @classmethod
    def get_available_extra_fields(cls):
        return [
            'client_id',
            'client_secret',
            'from_phone_number',
        ]

    @classmethod
    def get_api_id(cls):
        return 'ORANGE_SN'

    @classmethod
    def get_generic_name(cls):
        return "OrangeSN"

    @classmethod
    def get_form_class(cls):
        return OrangeSNBackendForm

    @classmethod
    def get_opt_in_keywords(cls):
        return ['START', 'UNSTOP']

    @classmethod
    def get_pass_through_opt_in_keywords(cls):
        return ['YES']

    @classmethod
    def get_opt_out_keywords(cls):
        return ['STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT']

    @classmethod
    def convert_to_whatsapp(cls, number):
        if number.startswith(WHATSAPP_PREFIX):
            return number
        return f"{WHATSAPP_PREFIX}{number}"

    @classmethod
    def convert_from_whatsapp(cls, number):
        return number.replace(WHATSAPP_PREFIX, "")

    def getToken(client_id, client_secret):
        response = requests.post('https://api.orange.com/oauth/v3/token',
            headers={
                    'Authorization': f"Basic {client_id}:{client_secret}",
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
            }, data={
                'grant_type': 'client_credentials'
            }
        )
        response = response.json()
        return response['access_token']


    def getUsageStats(token):
        response = requests.get('https://api.orange.com/sms/admin/v1/statistics',
            headers={
                'Authorization': f'Bearer {token}'
            }
        )
        stats = response.json()

        return stats


    def showBalanceSMS(token):
        response = requests.get('https://api.orange.com/sms/admin/v1/contracts',
            headers={
                'Authorization': f"Bearer {token}"
            }
        )
        balance = response.json()
        print(balance)

        return balance


    def send(self, msg, orig_phone_number=None, *args, **kwargs):
        config = self.config
        token = self.getToken(config.client_id, config.cient_secret)
        url = f'https://api.orange.com/smsmessaging/v1/outbound/tel:{senderAddress}/requests'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        data = {
            "outboundSMSMessageRequest":{
                "address": f"tel:{msg.phone_number}",
                "senderAddress":f"tel:{config.from_phone_number}",
                "outboundSMSTextMessage":{
                    "message": msg.text
            }
        }}
        response = requests.post(url, headers=headers, data=json.dumps(data))

        return response.json()


    def from_or_messaging_service_sid(self, phone_number: str) -> (Optional[str], Optional[str]):
        return phone_number, None

