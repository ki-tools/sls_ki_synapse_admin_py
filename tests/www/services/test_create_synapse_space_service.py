import pytest
import json
import os
from www.core import Synapse, Env
from www.services import CreateSynapseSpaceService
import synapseclient as syn


@pytest.fixture
def institution_name(syn_test_helper):
    return syn_test_helper.uniq_name()


@pytest.fixture
def user_identifier(syn_test_helper):
    return '{0}@test.com'.format(syn_test_helper.uniq_name())


@pytest.fixture
def agreement_url(syn_test_helper):
    return 'https://{0}/doc.pdf'.format(syn_test_helper.uniq_name())


@pytest.fixture
def emails(syn_test_helper):
    return [
        syn_test_helper.uniq_name(postfix='@test.com'),
        syn_test_helper.uniq_name(postfix='@test.com'),
        syn_test_helper.uniq_name(postfix='@test.com')
    ]


@pytest.fixture
def service(syn_test_helper, institution_name, user_identifier, agreement_url, emails):
    service = CreateSynapseSpaceService(institution_name,
                                        institution_name,
                                        user_identifier,
                                        agreement_url=agreement_url,
                                        emails=emails)

    yield service
    if service.project:
        syn_test_helper.dispose_of(service.project)
    if service.team:
        syn_test_helper.dispose_of(service.team)


@pytest.fixture
def assert_basic_service_success(syn_test_helper):
    def _fn(service):
        assert service.project is not None
        assert service.team is not None
        assert len(service.errors) == 0
        syn_test_helper.dispose_of(service.project)
        syn_test_helper.dispose_of(service.team)

    yield _fn


@pytest.fixture
def assert_basic_service_errors(syn_test_helper):
    def _fn(service):
        assert len(service.errors) > 0
        if service.project:
            syn_test_helper.dispose_of(service.project)
        if service.team:
            syn_test_helper.dispose_of(service.team)

    yield _fn


def test_it_creates_the_project(service, assert_basic_service_success):
    assert service.execute() == service
    assert_basic_service_success(service)


def test_it_does_not_create_a_duplicate_project(syn_test_helper,
                                                temp_file,
                                                user_identifier,
                                                assert_basic_service_errors):
    existing_project = syn_test_helper.create_project()
    service = CreateSynapseSpaceService(existing_project.name, existing_project.name, user_identifier)
    assert service.execute() == service
    assert_basic_service_errors(service)

    assert service.project is None
    assert len(service.errors) == 1
    assert service.errors[0] == 'Project with name: "{0}" already exists.'.format(existing_project.name)


def test_it_sets_the_storage_location(service, assert_basic_service_success, syn_client):
    assert service.execute() == service
    assert_basic_service_success(service)

    storage_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
    storage_setting = syn_client.getProjectSetting(service.project.id, 'upload')
    storage_ids = storage_setting.get('locations')
    assert storage_id in storage_ids


def test_it_creates_the_team(service, assert_basic_service_success):
    assert service.execute() == service
    assert_basic_service_success(service)

    assert service.team.name == service.project.name


def test_it_assigns_the_team_to_the_project(service, assert_basic_service_success, syn_client):
    assert service.execute() == service
    assert_basic_service_success(service)

    syn_perms = syn_client.getPermissions(service.project, principalId=service.team.id)
    assert syn_perms
    syn_perms.sort() == Synapse.CAN_EDIT_AND_DELETE_PERMS.sort()


def test_it_adds_managers_to_the_team(syn_client,
                                      monkeypatch,
                                      institution_name,
                                      user_identifier,
                                      emails,
                                      assert_basic_service_success):
    user_ids = [Env.Test.TEST_OTHER_SYNAPSE_USER_ID()]
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_TEAM_MANAGER_USER_IDS', ','.join([str(u) for u in user_ids]))

    service = CreateSynapseSpaceService(institution_name, institution_name, user_identifier)
    assert service.execute() == service
    assert_basic_service_success(service)

    syn_invites = syn_client.restGET('/team/{0}/openInvitation'.format(service.team.id))
    invite_results = syn_invites.get('results')

    assert len(invite_results) == len(user_ids)
    for result in invite_results:
        user_id = int(result.get('inviteeId'))
        assert user_id in user_ids

    team_acl = syn_client.restGET('/team/{0}/acl'.format(service.team.id))
    acl_accesses = team_acl.get('resourceAccess')
    for user_id in user_ids:
        resource = next((r for r in acl_accesses if r['principalId'] == user_id))
        assert resource.get('accessType').sort() == Synapse.TEAM_MANAGER_PERMISSIONS.sort()


def test_it_invites_the_emails_to_the_team(syn_client,
                                           institution_name,
                                           user_identifier,
                                           emails,
                                           assert_basic_service_success):
    service = CreateSynapseSpaceService(institution_name, institution_name, user_identifier, emails=emails)
    assert service.execute() == service
    assert_basic_service_success(service)

    syn_invites = syn_client.restGET('/team/{0}/openInvitation'.format(service.team.id))
    assert syn_invites
    invite_results = syn_invites.get('results')
    assert len(invite_results) == len(emails)
    for result in invite_results:
        email = result.get('inviteeEmail')
        assert email in emails


def test_it_grants_principals_access_to_the_project(service,
                                                    syn_test_helper,
                                                    syn_client,
                                                    monkeypatch,
                                                    assert_basic_service_success):
    test_user_id = Env.Test.TEST_OTHER_SYNAPSE_USER_ID()

    config = [
        {'id': test_user_id, 'permission': 'CAN_VIEW'},
        {'id': syn_test_helper.create_team().id, 'permission': 'ADMIN'},
        {'id': syn_test_helper.create_team().id, 'permission': 'CAN_EDIT'}
    ]

    config_str = '{0}:{1},{2}:{3},{4}:{5}'.format(
        config[0]['id'],
        config[0]['permission'],
        config[1]['id'],
        config[1]['permission'],
        config[2]['id'],
        config[2]['permission']
    )
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_GRANT_PROJECT_ACCESS', config_str)

    assert service.execute() == service
    assert_basic_service_success(service)

    for item in config:
        syn_perms = syn_client.getPermissions(service.project, principalId=item['id'])
        assert syn_perms
        syn_perms.sort() == Synapse.get_perms_by_code(item['permission']).sort()


def test_it_creates_the_folders(service, assert_basic_service_success, syn_client, monkeypatch):
    folder_names = ['one', 'two', 'three', 'four with a space', 'five with a space']
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_FOLDER_NAMES', ','.join(folder_names))

    assert service.execute() == service
    assert_basic_service_success(service)

    syn_children = list(syn_client.getChildren(service.project, includeTypes=['folder']))
    syn_folders = [c.get('name') for c in syn_children]
    assert syn_folders.sort() == folder_names.sort()


def test_it_creates_sub_folders(service, assert_basic_service_success, syn_client, monkeypatch):
    folder_names = ['one/two/three']
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_FOLDER_NAMES', ','.join(folder_names))

    assert service.execute() == service
    assert_basic_service_success(service)

    syn_children = list(syn_client.getChildren(service.project, includeTypes=['folder']))
    assert len(syn_children) == 1
    assert syn_children[0]['name'] == 'one'

    syn_children = list(syn_client.getChildren(syn_children[0]['id'], includeTypes=['folder']))
    assert len(syn_children) == 1
    assert syn_children[0]['name'] == 'two'

    syn_children = list(syn_client.getChildren(syn_children[0]['id'], includeTypes=['folder']))
    assert len(syn_children) == 1
    assert syn_children[0]['name'] == 'three'

    syn_children = list(syn_client.getChildren(syn_children[0]['id'], includeTypes=['folder']))
    assert len(syn_children) == 0


def test_it_creates_the_wiki(service, syn_test_helper, syn_client, monkeypatch, assert_basic_service_success):
    # Create a project with a wiki to copy.
    wiki_project = syn_test_helper.create_project()
    template_wiki = syn_test_helper.create_wiki(owner=wiki_project)
    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_WIKI_PROJECT_ID', wiki_project.id)

    assert service.execute() == service
    assert_basic_service_success(service)

    syn_wiki = syn_client.getWiki(service.project)
    assert syn_wiki.title == template_wiki.title
    assert syn_wiki.markdown == template_wiki.markdown


def test_it_writes_the_log_file_on_success(service,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch,
                                           user_identifier,
                                           assert_basic_service_success):
    project = syn_test_helper.create_project()
    folder = syn_client.store(syn.Folder(name='Synapse Admin Log', parent=project))

    monkeypatch.setenv('CREATE_SYNAPSE_SPACE_LOG_FOLDER_ID', folder.id)

    assert service.execute() == service
    assert_basic_service_success(service)

    files = list(Synapse.client().getChildren(folder))
    assert len(files) == 1

    file = Synapse.client().get(files[0]['id'])
    assert file.name.endswith('_create_space.json')
    with open(file.path, mode='r') as f:
        jdata = json.loads(f.read())

    jparms = jdata['parameters']
    assert jparms['project_name'] == service.project_name
    assert jparms['institution_name'] == service.institution_name
    assert jparms['agreement_url'] == service.agreement_url
    assert jparms['emails'] == service.emails
    assert jparms['user'] == user_identifier

    jproject = jdata['project']
    assert jproject['id'] == service.project.id
    assert jproject['name'] == service.project.name

    jteam = jdata['team']
    assert jteam['id'] == service.team.id
    assert jteam['name'] == service.team.name


def test_it_writes_the_log_file_on_failure(service,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch,
                                           assert_basic_service_success):
    # TODO:
    pass


def test_it_updates_the_contribution_agreement_table(syn_test_helper,
                                                     syn_client,
                                                     institution_name,
                                                     user_identifier,
                                                     agreement_url,
                                                     emails,
                                                     monkeypatch,
                                                     assert_basic_service_success):
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

    service = CreateSynapseSpaceService(institution_name,
                                        institution_name,
                                        user_identifier,
                                        agreement_url=agreement_url,
                                        emails=emails)
    assert service.execute() == service
    assert_basic_service_success(service)

    rows = list(syn_client.tableQuery(
        "select {0} from {1}".format(', '.join([c['name'] for c in cols]), syn_table.id))
    )

    assert len(rows) == 1
    row = rows[0]

    assert row[2] == institution_name
    assert row[3] == emails[0]
    assert row[4] == agreement_url
    assert row[5] == service.project.id
    assert str(row[6]) == str(service.team.id)


def test_it_fails_if_the_contribution_agreement_table_does_not_have_the_required_columns(service,
                                                                                         syn_test_helper,
                                                                                         syn_client,
                                                                                         monkeypatch,
                                                                                         assert_basic_service_errors):
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

    assert service.execute() == service
    assert_basic_service_errors(service)
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
