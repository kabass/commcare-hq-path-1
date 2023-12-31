import doctest

from nose.tools import assert_equal, assert_true

from corehq.apps.fixtures.models import Field, LookupTableRow
from custom.abt.reports import fixture_utils
from custom.abt.reports.fixture_utils import (
    dict_values_in,
    fixture_data_item_to_dict,
)


def test_dict_values_in_param_none():
    swallow = {'permutation': 'unladen'}
    result = dict_values_in(swallow, None)
    assert_true(result)


def test_dict_values_in_param_empty():
    swallow = {'permutation': 'unladen'}
    result = dict_values_in(swallow, {})
    assert_true(result)


def test_dict_values_in_value_none():
    swallow = {'permutation': 'unladen'}
    result = dict_values_in(swallow, {'permutation': None})
    assert_true(result)


def test_fixture_data_item_to_dict():
    data_item = LookupTableRow(
        domain='test-domain',
        fields={
            'id': [
                Field(
                    value='789abc',
                    properties={}
                )
            ],
            'name': [
                Field(
                    value='John',
                    properties={'lang': 'en'}
                ),
                Field(
                    value='Jan',
                    properties={'lang': 'nld'}
                ),
                Field(
                    value='Jean',
                    properties={'lang': 'fra'}
                ),
            ]
        }
    )
    dict_ = fixture_data_item_to_dict(data_item)
    assert_equal(dict_, {
        'id': '789abc',
        'name': 'John'
    })


def test_empty_fixture_data_item_to_dict():
    data_item = LookupTableRow(
        domain='test-domain',
        fields={'id': [], 'name': []}
    )
    dict_ = fixture_data_item_to_dict(data_item)
    assert_equal(dict_, {
        'id': None,
        'name': None,
    })


def test_doctests():
    results = doctest.testmod(fixture_utils)
    assert results.failed == 0
