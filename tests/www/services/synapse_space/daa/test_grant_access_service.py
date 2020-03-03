import pytest
import time
import json
from datetime import date, timedelta
from www.core import Synapse, Env
from www.services.synapse_space.daa import GrantAccessService
import synapseclient as syn


@pytest.fixture
def mk_service(syn_test_helper, syn_client, mk_uniq_real_email, monkeypatch):
    services = []

    def _mk(team_name=syn_test_helper.uniq_name(prefix='Team'),
            institution_name=syn_test_helper.uniq_name(prefix='Institution'),
            institution_short_name=syn_test_helper.uniq_name(prefix='Institution Short Name'),
            user_identifier=mk_uniq_real_email(),
            agreement_url='https://{0}/doc.pdf'.format(syn_test_helper.uniq_name()),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            comments=syn_test_helper.uniq_name(prefix='Comment'),
            with_all=False,
            with_data_collection=False,
            with_emails=False):

        data_collection_name = None
        emails = None

        if with_data_collection or with_all:
            project = syn_test_helper.create_project()
            folder = syn_client.store(syn.Folder(name='Folder', parent=project))
            collections = [
                {"name": "Collection 1", "entities": [{"name": project.name, "id": project.id}]},
                {"name": "Collection 2", "entities": [{"name": folder.name, "id": folder.id}]}
            ]
            monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_DATA_COLLECTIONS', json.dumps(collections))
            data_collection_name = collections[0]['name']

        if with_emails or with_all:
            emails = [mk_uniq_real_email(), mk_uniq_real_email()]

        service = GrantAccessService(team_name,
                                     institution_name,
                                     institution_short_name,
                                     data_collection_name,
                                     user_identifier,
                                     agreement_url=agreement_url,
                                     emails=emails,
                                     start_date=start_date,
                                     end_date=end_date,
                                     comments=comments)
        services.append(service)
        return service

    yield _mk
    for service in services:
        if service.team:
            syn_test_helper.dispose_of(service.team)


@pytest.fixture
def assert_basic_service_success(syn_test_helper):
    def _fn(service):
        assert service.team is not None
        assert len(service.errors) == 0
        syn_test_helper.dispose_of(service.team)

    yield _fn


@pytest.fixture
def assert_basic_service_errors(syn_test_helper):
    def _fn(service):
        assert len(service.errors) > 0
        if service.team:
            syn_test_helper.dispose_of(service.team)

    yield _fn


def test_it_creates_the_team(mk_service, assert_basic_service_success):
    service = mk_service()
    assert service.execute() == service
    assert_basic_service_success(service)
    assert service.team.name == service.team_name


def test_it_does_not_create_duplicate_teams(mk_service, assert_basic_service_errors, syn_test_helper):
    existing_team = syn_test_helper.create_team()
    service = mk_service(team_name=existing_team.name)
    assert service.execute() == service
    assert_basic_service_errors(service)

    assert service.team is None
    assert len(service.errors) == 1
    assert 'Error creating team:' in service.errors[0]


def test_it_assigns_the_team_to_the_synapse_entities_with_can_download_access(mk_service,
                                                                              assert_basic_service_success,
                                                                              syn_client):
    service = mk_service(with_data_collection=True)
    assert service.execute() == service
    assert_basic_service_success(service)

    assert service.data_collection is not None

    for syn_id in [c['id'] for c in service.data_collection['entities']]:
        syn_perms = syn_client.getPermissions(syn_id, principalId=service.team.id)
        assert syn_perms
        syn_perms.sort() == Synapse.CAN_DOWNLOAD_PERMS.sort()


def test_it_adds_managers_to_the_team(mk_service,
                                      assert_basic_service_success,
                                      syn_client,
                                      monkeypatch):
    user_ids = [Env.Test.TEST_OTHER_SYNAPSE_USER_ID()]
    monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_TEAM_MANAGER_USER_IDS', ','.join([str(u) for u in user_ids]))

    service = mk_service()
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
        assert resource.get('accessType').sort() == Synapse.TEAM_MANAGER_PERMS.sort()


def test_it_invites_the_emails_to_the_team(mk_service, assert_basic_service_success, syn_client):
    service = mk_service(with_emails=True)
    emails = service.emails
    assert len(emails) >= 1
    assert service.execute() == service
    assert_basic_service_success(service)

    syn_invites = syn_client.restGET('/team/{0}/openInvitation'.format(service.team.id))
    assert syn_invites
    invite_results = syn_invites.get('results')
    assert len(invite_results) == len(emails)
    for result in invite_results:
        email = result.get('inviteeEmail')
        assert email in emails


def test_it_writes_the_log_file_on_success(mk_service,
                                           assert_basic_service_success,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch):
    project = syn_test_helper.create_project()
    folder = syn_client.store(syn.Folder(name='Synapse Admin Log', parent=project))

    monkeypatch.setenv('SYNAPSE_SPACE_LOG_FOLDER_ID', folder.id)

    service = mk_service(with_all=True)
    assert service.institution_name is not None
    assert service.institution_short_name is not None
    assert service.data_collection_name is not None
    assert len(service.emails) >= 1
    assert service.agreement_url is not None
    assert service.start_date is not None
    assert service.end_date is not None
    assert service.comments is not None
    assert service.execute() == service
    assert_basic_service_success(service)

    files = list(Synapse.client().getChildren(folder))
    assert len(files) == 1

    file = Synapse.client().get(files[0]['id'])
    assert file.name.endswith('_daa_grant_access.json')
    with open(file.path, mode='r') as f:
        jdata = json.loads(f.read())

    jparms = jdata['parameters']
    assert jparms['team_name'] == service.team_name
    assert jparms['institution_name'] == service.institution_name
    assert jparms['institution_short_name'] == service.institution_short_name
    assert jparms['agreement_url'] == service.agreement_url
    assert jparms['emails'] == service.emails
    assert jparms['start_date'] == service.start_date.strftime('%Y-%m-%d')
    assert jparms['end_date'] == service.end_date.strftime('%Y-%m-%d')
    assert jparms['comments'] == service.comments
    assert jparms['user'] == service.user_identifier

    jteam = jdata['team']
    assert jteam['id'] == service.team.id
    assert jteam['name'] == service.team.name

    jdc = jdata['data_collection']
    assert jdc['name'] == service.data_collection['name']
    assert jdc['entities'] == service.data_collection['entities']


def test_it_writes_the_log_file_on_failure(mk_service,
                                           assert_basic_service_success,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch):
    # TODO:
    pass


def test_it_updates_the_access_agreement_table(mk_service,
                                               assert_basic_service_success,
                                               syn_test_helper,
                                               syn_client,
                                               monkeypatch):
    # Create a project with a table to update.
    table_project = syn_test_helper.create_project()
    cols = [
        syn.Column(name='Organization', columnType='STRING', maximumSize=200),
        syn.Column(name='Contact', columnType='STRING', maximumSize=200),
        syn.Column(name='Synapse_Team_ID', columnType='INTEGER'),
        syn.Column(name='Granted_Entity_IDs', columnType='STRING', maximumSize=1000),
        syn.Column(name='Agreement_Link', columnType='LINK', maximumSize=1000),
        syn.Column(name='Start_Date', columnType='DATE'),
        syn.Column(name='End_Date', columnType='DATE'),
        syn.Column(name='Comments', columnType='STRING', maximumSize=1000),
        syn.Column(name='Test_Col_One', columnType='STRING', maximumSize=50),
        syn.Column(name='Test_Col_Two', columnType='STRING', maximumSize=50)
    ]
    schema = syn.Schema(name='KiData_Access_Agreements', columns=cols, parent=table_project)
    syn_table = syn_client.store(schema)
    monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_AGREEMENT_TABLE_ID', syn_table.id)

    service = mk_service(with_all=True)
    assert service.data_collection_name is not None
    assert len(service.emails) >= 1
    assert service.agreement_url is not None
    assert service.start_date is not None
    assert service.end_date is not None
    assert service.comments is not None
    assert service.execute() == service
    assert_basic_service_success(service)

    rows = list(syn_client.tableQuery(
        "select {0} from {1}".format(', '.join([c['name'] for c in cols]), syn_table.id))
    )

    assert len(rows) == 1
    row = rows[0]

    assert row[2] == service.institution_name
    assert row[3] == service.emails[0]
    assert str(row[4]) == str(service.team.id)
    assert row[5] == ', '.join('{0} ({1})'.format(c['id'], c['name']) for c in service.data_collection['entities'])
    assert row[6] == service.agreement_url
    assert row[7].strftime('%Y-%m-%d') == service.start_date.strftime('%Y-%m-%d')
    assert row[8].strftime('%Y-%m-%d') == service.end_date.strftime('%Y-%m-%d')
    assert row[9] == service.comments


def test_it_fails_if_the_access_agreement_table_does_not_have_the_required_columns(mk_service,
                                                                                   assert_basic_service_errors,
                                                                                   syn_test_helper,
                                                                                   syn_client,
                                                                                   monkeypatch):
    # Create a project with a table to update.
    table_project = syn_test_helper.create_project()
    cols = [
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200),
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200),
        syn.Column(name=syn_test_helper.uniq_name(), columnType='STRING', maximumSize=200)
    ]
    schema = syn.Schema(name='KiData_Access_Agreements', columns=cols, parent=table_project)
    syn_table = syn_client.store(schema)
    monkeypatch.setenv('SYNAPSE_SPACE_DAA_GRANT_ACCESS_AGREEMENT_TABLE_ID', syn_table.id)

    service = mk_service()
    assert service.execute() == service
    assert_basic_service_errors(service)
    assert service.errors
    assert len(service.errors) == 1
    assert 'Column: Organization does not exist in table' in service.errors[0]


###############################################################################
# Validations
###############################################################################

def test_validations_validate_team_name(syn_test_helper, syn_client):
    existing_team = syn_test_helper.create_team(prefix='Team ')

    # Wait for the team to be available from Synapse before checking.
    tries = 0
    while True:
        tries += 1
        try:
            syn_client.getTeam(existing_team.name)
            break
        except ValueError:
            if tries >= 10:
                break
            else:
                time.sleep(3)

    error = GrantAccessService.Validations.validate_team_name(existing_team.name)
    assert error == 'Team with name: "{0}" already exists.'.format(existing_team.name)
