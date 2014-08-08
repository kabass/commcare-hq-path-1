"""
Fluff calculators that pertain to specific cases/beneficiaries (mothers)
These are used in the Beneficiary Payment Report and Conditions Met Report
"""
import re
import datetime
from decimal import Decimal

from couchdbkit.exceptions import ResourceNotFound
from dimagi.utils.decorators.memoized import memoized
from django.utils.translation import ugettext as _

from corehq.apps.users.models import CommCareCase
from corehq.util.translation import localize

from .constants import *


EMPTY_FIELD = "---"
M_ATTENDANCE_Y = 'attendance_vhnd_y.png'
M_ATTENDANCE_N = 'attendance_vhnd_n.png'
C_ATTENDANCE_Y = 'child_attendance_vhnd_y.png'
C_ATTENDANCE_N = 'child_attendance_vhnd_n.png'
M_WEIGHT_Y = 'woman_checking_weight_yes.png'
M_WEIGHT_N = 'woman_checking_weight_no.png'
C_WEIGHT_Y = 'child_weight_y.png'
C_WEIGHT_N = 'child_weight_n.png'
MEASLEVACC_Y = 'child_child_measlesvacc_y.png'
MEASLEVACC_N = 'child_child_measlesvacc_n.png'
C_REGISTER_Y = 'child_child_register_y.png'
C_REGISTER_N = 'child_child_register_n.png'
CHILD_WEIGHT_Y = 'child_weight_2_y.png'
CHILD_WEIGHT_N = 'child_weight_2_n.png'
IFA_Y = 'ifa_receive_y.png'
IFA_N = 'ifa_receive_n.png'
EXCBREASTFED_Y = 'child_child_excbreastfed_y.png'
EXCBREASTFED_N = 'child_child_excbreastfed_n.png'
ORSZNTREAT_Y = 'child_orszntreat_y.png'
ORSZNTREAT_N = 'child_orszntreat_n.png'
GRADE_NORMAL_Y = 'grade_normal_y.png'
GRADE_NORMAL_N = 'grade_normal_n.png'
SPACING_PROMPT_Y = 'birth_spacing_prompt_y.png'
SPACING_PROMPT_N = 'birth_spacing_prompt_n.png'


# TODO Sravan, aren't these fixtures?
MONTH_AMT = 250
TWO_YEAR_AMT = 2000
THREE_YEAR_AMT = 3000

class OPMCase(object):

    def condition_image(self, image_y, image_n, condition):
        if condition is None:
            return ''
        elif condition is True:
            return self.img_elem % image_y
        elif condition is False:
            return self.img_elem % image_n

    @property
    @memoized
    def form_properties(self):
        properties = {
            'window_1_1': None,
            'window_1_2': None,
            'window_2_1': None,
            'window_2_2': None,
            'attendance_vhnd_3': None,
            'attendance_vhnd_6': None,
            'child1_vhndattend_calc': None,
            'prev_child1_vhndattend_calc': None,
            'child1_attendance_vhnd': None,
            'weight_tri_1': None,
            'prev_weight_tri_1': None,
            'weight_tri_2': None,
            'prev_weight_tri_2': None,
            'child1_growthmon_calc': None,
            'prev_child1_growthmon_calc': None,
            'child1_excl_breastfeed_calc': None,
            'prev_child1_excl_breastfeed_calc': None,
            'child1_ors_calc': None,
            'prev_child1_ors_calc': None,
            'child1_weight_calc': None,
            'child1_register_calc': None,
            'child1_measles_calc': None,
            'prev_child1_weight_calc': None,
            'prev_child1_register_calc': None,
            'prev_child1_measles_calc': None,
            'child1_suffer_diarrhea': None,
            'interpret_grade_1': None,
        }
        for form in self.forms:
            if self.datespan.startdate <= form.received_on <= self.datespan.enddate:
                for prop in properties:
                    if prop in ['child1_suffer_diarrhea', 'child1_growthmon_calc', 'prev_child1_growthmon_calc']:
                        if 'child_1' in form.form and prop in form.form['child_1']:
                            properties[prop] = form.form['child_1'][prop]
                    else:
                        # TODO is this right?  Multiple matching forms will overwrite
                        if prop in form.form:
                            properties[prop] = form.form[prop]
        return properties

    @property
    def preg_attended_vhnd(self):
        if self.preg_month != 9:
            vhnd_attendance = {
                4: self.case_property('attendance_vhnd_1', 0),
                5: self.case_property('attendance_vhnd_2', 0),
                6: self.case_property('attendance_vhnd_3', 0),
                7: self.case_property('month_7_attended', 0),
                8: self.case_property('month_8_attended', 0)
            }
            # TODO don't 500 on bad key
            return vhnd_attendance[self.preg_month] == '1'

    # TODO abstract this pattern of looking for received in form_property s
    # and in case_property s
    @property
    def child_attended_vhnd(self):
        if self.child_age != 1:
            return 'received' in [
                self.form_properties['child1_vhndattend_calc'],
                self.form_properties['prev_child1_vhndattend_calc'],
                self.form_properties['child1_attendance_vhnd']
            ]

    @property
    def preg_weighed(self):
        if self.preg_month in [6, 9]:
            return 'received' in [
                self.case_property('weight_tri_1', 0),
                self.case_property('prev_weight_tri_1', 0)
            ]

    @property
    def child_growth_calculated(self):
        if self.child_age % 3 == 0:
            return 'received' in [
                self.form_properties['child1_growthmon_calc'],
                self.form_properties['prev_child1_growthmon_calc']
            ]

    @property
    def preg_received_ifa(self):
        if self.preg_month == 6:
            if self.block== "atri":
                return self.case_property('ifa_tri_1', 0) == 'received'

    @property
    def child_received_ors(self):
        if self.child_age % 3 == 0:
            if self.form_properties['child1_suffer_diarrhea'] == '1':
                return 'received' in [
                    self.form_properties['child1_ors_calc'],
                    self.form_properties['prev_child1_ors_calc']
                ]

    @property
    def child_condition_four(self):
        # TODO This appears to be one of several unrelated conditions
        # depending on the child's age, I think it's wrong
        if self.block == 'atri':
            if self.child_age == 3:
                # TODO reformat
                prev_forms = [form for form in self.forms
                        if (self.datespan.startdate - datetime.timedelta(90))
                            <= form.received_on <= self.datespan.enddate]
                weight_key = "child1_child_weight"
                child_forms = [form.form["child_1"] for form in prev_forms
                        if "child_1" in form.form]
                birth_weight = [child[weight_key] for child in child_forms if weight_key in child]
                child_birth_weight_taken = '1' in birth_weight
                return child_birth_weight_taken
            elif self.child_age == 6:
                return 'received' in [
                    self.form_properties['child1_register_calc'],
                    self.form_properties['prev_child1_register_calc']
                ]
            elif self.child_age == 12:
                return 'received' in [
                    self.form_properties['child1_measles_calc'],
                    self.form_properties['prev_child1_measles_calc']
                ]

    @property
    def child_breastfed(self):
        if self.child_age == 6 and self.block == 'atri':
            # TODO reformat this whole thing
            prev_forms = [form for form in self.forms
                    if (self.datespan.startdate - datetime.timedelta(180))
                        <= form.received_on <= self.datespan.enddate]
            excl_key = "child1_child_excbreastfed"
            child_forms = [form.form["child_1"] for form in prev_forms if "child_1" in form.form]
            exclusive_breastfed = [child[excl_key] for child in child_forms if excl_key in child]
            # FIXME This can't possibly be right
            child_excusive_breastfed = exclusive_breastfed == ['1', '1', '1', '1', '1', '1']
            return child_excusive_breastfed

    @property
    def year_end_condition(self):
        if self.block == 'wazirganj':
            return '1' in self.birth_spacing_prompt
        else:
            return self.form_properties['interpret_grade_1'] is 'normal'

    def __init__(self, case, report):
        self.case = case
        self.report = report
        self.block = report.block.lower()
        self.datespan = self.report.datespan

        if report.snapshot is not None:
            report.filter(
                lambda key: case['_source'][key],
                # case.awc_name, case.block_name
                [('awc_name', 'awcs'), ('block_name', 'block'), ('owner_id', 'gp'), ('closed', 'is_open')],
            )
        if not report.is_rendered_as_email:
            self.img_elem = '<div style="width:100px !important;"><img src="/static/opm/img/%s"></div>'
        else:
            self.img_elem = '<div><img src="/static/opm/img/%s"></div>'

        # TODO get rid of this altogether and just wrap the ES result
        try:
            self.case_obj = CommCareCase.get(case['_source']['_id'])
        except ResourceNotFound:
            raise InvalidRow

        # TODO move this to initial query
        if self.case_obj.closed and self.case_obj.closed_on <= self.datespan.startdate_utc:
            print "*"*40, 'ESOE: Case closed problem', "*"*40
            raise InvalidRow

        self.set_case_properties()

        if report.is_rendered_as_email:
            with localize('hin'):
                self.status = _(self.status)

    def case_property(self, name, default=None):
        if name in self.case_obj:
            if type(self.case_obj[name]) is dict:
                return self.case_obj[name]
            return self.case_obj[name]
        else:
            return default if default is not None else EMPTY_FIELD

    def set_case_properties(self):
        # TODO clean up this block
        reporting_date = datetime.date(self.report.year, self.report.month + 1, 1) - datetime.timedelta(1)
        status = "unknown"
        self.preg_month = -1
        self.child_age = -1
        window = -1
        dod_date = self.case_property('dod', EMPTY_FIELD)
        edd_date = self.case_property('edd', EMPTY_FIELD)
        if dod_date == EMPTY_FIELD and edd_date == EMPTY_FIELD:
            raise InvalidRow
        if dod_date and dod_date != EMPTY_FIELD:
            if dod_date >= reporting_date:
                status = 'pregnant'
                self.preg_month = 9 - (dod_date - reporting_date).days / 30 # edge case
            elif dod_date < reporting_date:
                status = 'mother'
                self.child_age = 1 + (reporting_date - dod_date).days / 30
        elif edd_date and edd_date != EMPTY_FIELD:
            if edd_date >= reporting_date:
                status = 'pregnant'
                self.preg_month = 9 - (edd_date - reporting_date).days / 30
            elif edd_date < reporting_date: # edge case
                raise InvalidRow
        if status == 'pregnant' and (self.preg_month > 3 and self.preg_month < 10):
            self.window = (self.preg_month - 1) / 3
        elif status == 'mother' and (self.child_age > 0 and self.child_age < 37):
            self.window = (self.child_age - 1) / 3 + 1
        else:
            raise InvalidRow
        if (self.child_age == -1 and self.preg_month == -1):
            print "?"*40, 'ESOE: InvalidRow', "?"*40
            print "Is this ever executed?"
            raise InvalidRow

        self.status = status

        self.name = self.case_property('name', EMPTY_FIELD)
        self.awc_name = self.case_property('awc_name', EMPTY_FIELD)
        self.block_name = self.case_property('block_name', EMPTY_FIELD)
        self.husband_name = self.case_property('husband_name', EMPTY_FIELD)
        self.bank_name = self.case_property('bank_name', EMPTY_FIELD)
        self.ifs_code = self.case_property('ifsc', EMPTY_FIELD)
        self.village = self.case_property('village_name', EMPTY_FIELD)
        self.owner_id = self.case_property('owner_id', EMPTY_FIELD)
        self.case_id = self.case_property('_id', EMPTY_FIELD)
        self.owner_id = self.case_property('owner_id', '')
        self.closed = self.case_property('closed', False)

        account = self.case_property('bank_account_number', None)
        if isinstance(account, Decimal):
            account = int(account)
        self.account_number = unicode(account) if account else ''
        # fake cases will have accounts beginning with 111
        if re.match(r'^111', self.account_number):
            raise InvalidRow

    @property
    @memoized
    def forms(self):
        return self.case_obj.get_forms()

    @property
    def all_conditions_met(self):
        # TODO Sravan, please confirm this logic
        return True

    @property
    def month_amt(self):
        return MONTH_AMT if self.all_conditions_met else 0

    @property
    def spacing_cash(self):
        # TODO Sravan, please confirm this logic
        if self.block == 'atri' and self.year_end_condition:
            if self.child_age == 24:
                return TWO_YEAR_AMT
            elif self.child_age == 36:
                return THREE_YEAR_AMT
        return 0

    @property
    def cash_amt(self):
        return self.month_amt + self.spacing_cash

    @property
    def cash(self):
        cash_html = '<span style="color: {color};">Rs. {amt}</span>'
        return cash_html.format(
            color="red" if self.cash_amt == 0 else "green",
            amt=self.cash_amt,
        )


class ConditionsMet(OPMCase):
    method_map = {
        "atri": [
            ('name', _("List of Beneficiary"), True),
            ('awc_name', _("AWC Name"), True),
            ('block_name', _("Block Name"), True),
            ('husband_name', _("Husband Name"), True),
            ('status', _("Current status"), True),
            ('preg_month', _('Pregnancy Month'), True),
            ('child_age', _("Child Age"), True),
            ('window', _("Window"), True),
            ('one', _("1"), True),
            ('two', _("2"), True),
            ('three', _("3"), True),
            ('four', _("4"), True),
            ('five', _("5"), True),
            ('cash', _("Payment Amount"), True),
            ('case_id', _('Case ID'), True),
            ('owner_id', _("Owner Id"), False),
            ('closed', _('Closed'), False)
        ],
        'wazirganj': [
            ('name', _("List of Beneficiary"), True),
            ('awc_name', _("AWC Name"), True),
            ('block_name', _("Block Name"), True),
            ('husband_name', _("Husband Name"), True),
            ('status', _("Current status"), True),
            ('preg_month', _('Pregnancy Month'), True),
            ('child_age', _("Child Age"), True),
            ('window', _("Window"), True),
            ('one', _("1"), True),
            ('two', _("2"), True),
            ('three', _("3"), True),
            ('four', _("4"), True),
            ('cash', _("Payment Amount"), True),
            ('case_id', _('Case ID'), True),
            ('owner_id', _("Owner Id"), False),
            ('closed', _('Closed'), False)
        ]
    }

    def __init__(self, *args, **kwargs):
        super(ConditionsMet, self).__init__(*args, **kwargs)
        if self.status == 'mother':
            self.birth_spacing_prompt = []
            for form in self.forms:
                if 'birth_spacing_prompt' in form.form:
                    self.birth_spacing_prompt.append(form.form['birth_spacing_prompt'])
            self.preg_month = EMPTY_FIELD
            self.one = self.condition_image(C_ATTENDANCE_Y, C_ATTENDANCE_N, self.child_attended_vhnd)
            self.two = self.condition_image(C_WEIGHT_Y, C_WEIGHT_N, self.child_growth_calculated)
            self.three = self.condition_image(ORSZNTREAT_Y, ORSZNTREAT_N, self.child_received_ors)
            self.four = self.condition_image(MEASLEVACC_Y, MEASLEVACC_N, self.child_condition_four)
            self.five = self.condition_image(EXCBREASTFED_Y, EXCBREASTFED_N, self.child_breastfed)
        elif self.status == 'pregnant':
            self.one = self.condition_image(M_ATTENDANCE_Y, M_ATTENDANCE_N, self.preg_attended_vhnd)
            self.two = self.condition_image(M_WEIGHT_Y, M_WEIGHT_N, self.preg_weighed)
            self.three = self.condition_image(IFA_Y, IFA_N, self.preg_received_ifa)
            self.four = ''
            if self.block == 'wazirganj':
                if self.child_age > 23 and '1' in self.birth_spacing_prompt:
                    self.five = self.img_elem % SPACING_PROMPT_Y
                else:
                    self.five = self.img_elem % SPACING_PROMPT_N
            else:
                self.five = ''

        # This is what I think is meant by this stuff
        # https://github.com/dimagi/commcare-hq/blob/cacf077042edb23c1167563c5127b810dbcd555a/custom/opm/opm_reports/conditions_met.py#L297-L314
        if self.child_age in (24, 36):
            year_end_condition_img_Y = (SPACING_PROMPT_Y if self.block is 'wazirganj' else GRADE_NORMAL_Y)
            year_end_condition_img_N = (SPACING_PROMPT_N if self.block is 'wazirganj' else GRADE_NORMAL_N)
            if self.year_end_condition:
                self.five = self.img_elem % year_end_condition_img_Y
            else:
                self.five = self.img_elem % year_end_condition_img_N


class Beneficiary(OPMCase):
    """
    Constructor object for each row in the Beneficiary Payment Report
    """
    method_map = [
        # If you need to change any of these names, keep the key intact
        ('name', _("List of Beneficiaries"), True),
        ('husband_name', _("Husband Name"), True),
        ('awc_name', _("AWC Name"), True),
        ('bank_name', _("Bank Name"), True),
        ('ifs_code', _("IFS Code"), True),
        ('account_number', _("Bank Account Number"), True),
        ('block', _("Block Name"), True),
        ('village', _("Village Name"), True),
        ('bp1_cash', _("Birth Preparedness Form 1"), True),
        ('bp2_cash', _("Birth Preparedness Form 2"), True),
        ('delivery_cash', _("Delivery Form"), True),
        ('child_cash', _("Child Followup Form"), True),
        ('spacing_cash', _("Birth Spacing Bonus"), True),
        ('total', _("Amount to be paid to beneficiary"), True),
        ('owner_id', _("Owner ID"), False)
    ]

    def __init__(self, *args, **kwargs):
        super(Beneficiary, self).__init__(*args, **kwargs)
        # TODO
        self.bp1_cash = MONTH_AMT if self.bp1 else 0
        self.bp2_cash = MONTH_AMT if self.bp2 else 0
        self.delivery_cash = MONTH_AMT if self.delivery else 0
        self.child_cash = MONTH_AMT if self.chlid_followup else 0
        self.total = min(250, self.bp1_cash, self.bp2_cash, self.delivery_cash,
            self.child_cash)

        MONTH_AMT = 250
        TWO_YEAR_AMT = 2000
        THREE_YEAR_AMT = 3000

    @property
    def bp1(self):
        if self.block == 'atri':
            properties = ['window_1_1', 'window_1_2', 'window_1_3']
        else:
            properties = ['window_1_1', 'window_1_2', 'soft_window_1_3']
        for prop in properties:
            if self.form_properties[prop] == '1':
                return True
        return False

    @property
    def bp2(self):
        if self.block == 'atri':
            properties = ['window_2_1', 'window_2_2', 'window_2_3']
        else:
            properties = ['window_2_1', 'window_2_2', 'soft_window_2_3']
        for prop in properties:
            if self.form_properties[prop] == '1':
                return True
        return False

    @property
    def delivery(self):
        for form in self.forms:
            if form.xmlns == DELIVERY_XMLNS:
                if form.form.get('mother_preg_outcome') in ['2', '3']:
                    return True
        return False

    @property
    def child_followup(self):
        # WIP
        xmlns_list = children_forms + [CHILD_FOLLOWUP_XMLNS]
        if form.xmlns in children_forms:
            block = block_type(form)
            followed_up = False
            if block == "soft" and "total_soft_conditions" in form.form and form.form["total_soft_conditions"] == 1:
                yield case_date_group(form)
            else:
                for prop in [
                    'window%d_child%d' % (window, child)
                    for window in range(3, 15) for child in range(1, 4)
                ]:
                    if form.form.get(prop) == 1 and block == 'hard':
                        followed_up = True
                    elif form.form.get(prop) and block not in ['hard', 'soft']:
                        followed_up = True
                if followed_up:
                    yield case_date_group(form)


