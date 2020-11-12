import pytest
from www.server import app
from www.views.synapse_space.dca.forms import CreateDcaSynapseSpaceForm


def test_it_sets_the_project_name(client, dca_config):
    with app.test_request_context():
        form = CreateDcaSynapseSpaceForm()
        surname = 'AbcZ'
        form.field_pi_surname.data = surname

        for short_name, expected_name in [
            ('test', 'test_{0}'.format(surname)),
            ('   test   ', 'test_{0}'.format(surname)),
            ('test.1', 'test1_{0}'.format(surname)),
            ('test-1', 'test_1_{0}'.format(surname)),
            ('test 1', 'test_1_{0}'.format(surname)),
            ('test 1_ . - ', 'test_1_____{0}'.format(surname))
        ]:
            form.field_institution_short_name.data = short_name
            form.try_set_project_name()
            assert form.project_name == expected_name

        # Test additional_parties
        add_party_codes = [a['code'] for a in dca_config['additional_parties']]
        add_party_codes_str = '_'.join(add_party_codes)
        for short_name, expected_name in [
            ('test', '{0}_test_{1}'.format(add_party_codes_str, surname)),
            ('   test   ', '{0}_test_{1}'.format(add_party_codes_str, surname)),
            ('test.1', '{0}_test1_{1}'.format(add_party_codes_str, surname)),
            ('test-1', '{0}_test_1_{1}'.format(add_party_codes_str, surname)),
            ('test 1', '{0}_test_1_{1}'.format(add_party_codes_str, surname)),
            ('test 1_ . - ', '{0}_test_1_____{1}'.format(add_party_codes_str, surname))
        ]:
            form.field_institution_short_name.data = short_name
            form.field_institution_add_party.data = add_party_codes
            form.try_set_project_name()
            assert form.project_name == expected_name
