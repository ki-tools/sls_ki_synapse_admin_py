import pytest
from wtforms.validators import ValidationError

from www.server import app
from www.views.synapse_space.basic.forms import CreateBasicSynapseSpaceForm


def test_it_validates_the_project_name(client, syn_test_helper):
    with app.test_request_context():
        form = CreateBasicSynapseSpaceForm()

        existing_project = syn_test_helper.create_project()

        form.field_project_name.data = syn_test_helper.uniq_name(prefix='Project_')
        form.validate_field_project_name(form.field_project_name)

        with pytest.raises(ValidationError) as ex:
            form.field_project_name.data = existing_project.name
            form.validate_field_project_name(form.field_project_name)


def test_it_validates_the_team_name(client, syn_test_helper):
    with app.test_request_context():
        form = CreateBasicSynapseSpaceForm()

        existing_team = syn_test_helper.create_team()

        form.field_team_name.data = syn_test_helper.uniq_name(prefix='Team_')
        form.validate_field_team_name(form.field_team_name)

        with pytest.raises(ValidationError) as ex:
            form.field_team_name.data = existing_team.name
            form.validate_field_team_name(form.field_team_name)
