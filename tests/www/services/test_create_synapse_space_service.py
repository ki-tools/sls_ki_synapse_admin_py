import pytest
from www.core import Synapse, Env
from www.services import CreateSynapseSpaceService
import synapseclient as syn


def assert_basic_service_success(syn_test_helper, service):
    assert service.project is not None
    assert service.team is not None
    assert len(service.errors) == 0
    syn_test_helper.dispose_of(service.project)
    syn_test_helper.dispose_of(service.team)


def assert_basic_service_errors(syn_test_helper, service):
    assert len(service.errors) > 0
    if service.project:
        syn_test_helper.dispose_of(service.project)
    if service.team:
        syn_test_helper.dispose_of(service.team)


def test_it_creates_the_project(syn_test_helper):
    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)


def test_it_does_not_create_a_duplicate_project(syn_test_helper, temp_file):
    existing_project = syn_test_helper.create_project()
    service = CreateSynapseSpaceService(existing_project.name, existing_project.name)
    assert service.execute() == service
    assert_basic_service_errors(syn_test_helper, service)

    assert service.project is None
    assert len(service.errors) == 1
    assert service.errors[0] == 'Project with name: "{0}" already exists.'.format(existing_project.name)


def test_it_sets_the_storage_location(syn_test_helper, syn_client):
    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    storage_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
    storage_setting = syn_client.getProjectSetting(service.project.id, 'upload')
    storage_ids = storage_setting.get('locations')
    assert storage_id in storage_ids


def test_it_creates_the_team(syn_test_helper):
    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    assert service.team.name == service.project.name


def test_it_assigns_the_team_to_the_project(syn_test_helper, syn_client):
    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    syn_perms = syn_client.getPermissions(service.project, principalId=service.team.id)
    assert syn_perms
    syn_perms.sort() == Synapse.CAN_EDIT_AND_DELETE_PERMS.sort()


def test_it_invites_the_emails_to_the_team(syn_test_helper, syn_client):
    emails = [
        syn_test_helper.uniq_name(postfix='@test.com'),
        syn_test_helper.uniq_name(postfix='@test.com')
    ]

    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name, emails=emails)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    syn_invites = syn_client.restGET('/team/{0}/openInvitation'.format(service.team.id))
    assert syn_invites
    invite_results = syn_invites.get('results')
    assert len(invite_results) == len(emails)
    for result in invite_results:
        email = result.get('inviteeEmail')
        assert email in emails


def test_it_adds_the_admin_teams_to_the_project(syn_test_helper, syn_client, monkeypatch):
    # Create some teams to test with
    syn_admin_teams = [
        syn_test_helper.create_team(),
        syn_test_helper.create_team()
    ]
    syn_admin_team_ids = list(map(lambda t: t.id, syn_admin_teams))
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_ADMIN_TEAM_IDS', ','.join(syn_admin_team_ids))

    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    for syn_admin_team_id in syn_admin_team_ids:
        syn_perms = syn_client.getPermissions(service.project, principalId=syn_admin_team_id)
        assert syn_perms
        syn_perms.sort() == Synapse.CAN_EDIT_AND_DELETE_PERMS.sort()


def test_it_creates_the_folders(syn_test_helper, syn_client):
    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    syn_children = list(syn_client.getChildren(service.project, includeTypes=['folder']))
    syn_folders = list(map(lambda f: f.get('name'), syn_children))
    assert syn_folders.sort() == CreateSynapseSpaceService.DEFAULT_FOLDER_NAMES.sort()


def test_it_creates_the_wiki(syn_test_helper, syn_client, monkeypatch):
    # Create a project with a wiki to copy.
    wiki_project = syn_test_helper.create_project()
    template_wiki = syn_test_helper.create_wiki(owner=wiki_project)
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_DEFAULT_WIKI_PROJECT_ID', wiki_project.id)

    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    syn_wiki = syn_client.getWiki(service.project)
    assert syn_wiki.title == template_wiki.title
    assert syn_wiki.markdown == template_wiki.markdown


def test_it_updates_the_contribution_agreement_table(syn_test_helper, syn_client, monkeypatch):
    # Create a project with a table to update.
    table_project = syn_test_helper.create_project()
    cols = [
        syn.Column(name='Organization', columnType='STRING', maximumSize=200),
        syn.Column(name='Contact', columnType='STRING', maximumSize=200),
        syn.Column(name='Agreement_Link', columnType='LINK', maximumSize=1000),
        syn.Column(name='Synapse_Project_ID', columnType='ENTITYID'),
        syn.Column(name='Synapse_Team_ID', columnType='INTEGER'),
        syn.Column(name='Test_Col_One', columnType='STRING', maximumSize=50),
        syn.Column(name='Test_Col_Two', columnType='STRING', maximumSize=50)
    ]
    schema = syn.Schema(name='KiData_Contribution_Agreements', columns=cols, parent=table_project)
    syn_table = syn_client.store(schema)
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_CONTRIBUTION_AGREEMENT_TABLE_ID', syn_table.id)

    emails = [
        syn_test_helper.uniq_name(postfix='@test.com'),
        syn_test_helper.uniq_name(postfix='@test.com')
    ]

    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name, emails=emails)
    assert service.execute() == service
    assert_basic_service_success(syn_test_helper, service)

    rows = list(syn_client.tableQuery("select * from {0}".format(syn_table.id)))
    assert len(rows) == 1
    row = rows[0]
    assert row[2] == inst_name
    assert row[3] == emails[0]
    assert row[4] is None
    assert row[5] == service.project.id
    assert str(row[6]) == str(service.team.id)


def test_it_fails_if_the_contribution_agreement_table_does_not_have_the_required_columns(syn_test_helper,
                                                                                         syn_client,
                                                                                         monkeypatch):
    # Create a project with a table to update.
    table_project = syn_test_helper.create_project()
    cols = [
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200),
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200),
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200)
    ]
    schema = syn.Schema(name='KiData_Contribution_Agreements', columns=cols, parent=table_project)
    syn_table = syn_client.store(schema)
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_CONTRIBUTION_AGREEMENT_TABLE_ID', syn_table.id)

    inst_name = syn_test_helper.uniq_name()
    service = CreateSynapseSpaceService(inst_name, inst_name)
    assert service.execute() == service
    assert_basic_service_errors(syn_test_helper, service)
    assert service.errors
    assert len(service.errors) == 1
    assert 'Column: Organization does not exist in table' in service.errors[0]


###############################################################################
# Validations
###############################################################################

def test_validations_validate_project_name(syn_test_helper):
    existing_project = syn_test_helper.create_project()
    error = CreateSynapseSpaceService.Validations.validate_project_name(existing_project.name)
    assert error == 'Project with name: "{0}" already exists.'.format(existing_project.name)
