import pytest
from www.server import app
from www.views.synapse_space.daa.forms import GrantSynapseAccessForm


def test_it_sets_the_team_name(client, daa_config, set_daa_config):
    with app.test_request_context():
        form = GrantSynapseAccessForm()
        data_collection_name = daa_config['data_collections'][0]['name']
        form.field_data_collection.data = data_collection_name

        expected_collection_name = data_collection_name.replace(' ', '_')

        for short_name, expected_name in [
            ('test', 'KiAccess_{0}_test'.format(expected_collection_name)),
            ('   test   ', 'KiAccess_{0}_test'.format(expected_collection_name)),
            ('test.1', 'KiAccess_{0}_test1'.format(expected_collection_name)),
            ('test-1', 'KiAccess_{0}_test_1'.format(expected_collection_name)),
            ('test 1', 'KiAccess_{0}_test_1'.format(expected_collection_name)),
            ('test 1_ . - ', 'KiAccess_{0}_test_1____'.format(expected_collection_name))
        ]:
            form.field_institution_short_name.data = short_name
            form.try_set_team_name()
            assert form.team_name == expected_name

        # Test additional_parties
        add_party_codes = [a['code'] for a in daa_config['additional_parties']]
        add_party_codes_str = '_'.join(add_party_codes)
        for short_name, expected_name in [
            ('test', 'KiAccess_{0}_{1}_test'.format(expected_collection_name, add_party_codes_str)),
            ('   test   ', 'KiAccess_{0}_{1}_test'.format(expected_collection_name, add_party_codes_str)),
            ('test.1', 'KiAccess_{0}_{1}_test1'.format(expected_collection_name, add_party_codes_str)),
            ('test-1', 'KiAccess_{0}_{1}_test_1'.format(expected_collection_name, add_party_codes_str)),
            ('test 1', 'KiAccess_{0}_{1}_test_1'.format(expected_collection_name, add_party_codes_str)),
            ('test 1_ . - ', 'KiAccess_{0}_{1}_test_1____'.format(expected_collection_name, add_party_codes_str))
        ]:
            form.field_institution_short_name.data = short_name
            form.field_institution_add_party.data = add_party_codes
            form.try_set_team_name()
            assert form.team_name == expected_name

        form.field_institution_add_party.data = None

        # Test include_collection_name_in_team_name
        daa_config['data_collections'][0]['include_collection_name_in_team_name'] = False
        set_daa_config([daa_config])
        for short_name, expected_name in [
            ('test', 'KiAccess_test'),
            ('   test   ', 'KiAccess_test'),
            ('test.1', 'KiAccess_test1'),
            ('test-1', 'KiAccess_test_1'),
            ('test 1', 'KiAccess_test_1'),
            ('test 1_ . - ', 'KiAccess_test_1____')
        ]:
            form.field_institution_short_name.data = short_name
            form.try_set_team_name()
            assert form.team_name == expected_name

        # Test additional_parties with include_collection_name_in_team_name
        for short_name, expected_name in [
            ('test', 'KiAccess_{0}_test'.format(add_party_codes_str)),
            ('   test   ', 'KiAccess_{0}_test'.format(add_party_codes_str)),
            ('test.1', 'KiAccess_{0}_test1'.format(add_party_codes_str)),
            ('test-1', 'KiAccess_{0}_test_1'.format(add_party_codes_str)),
            ('test 1', 'KiAccess_{0}_test_1'.format(add_party_codes_str)),
            ('test 1_ . - ', 'KiAccess_{0}_test_1____'.format(add_party_codes_str))
        ]:
            form.field_institution_short_name.data = short_name
            form.field_institution_add_party.data = add_party_codes
            form.try_set_team_name()
            assert form.team_name == expected_name
