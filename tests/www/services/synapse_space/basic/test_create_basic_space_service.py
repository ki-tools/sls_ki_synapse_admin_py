import pytest
import json
from datetime import date, timedelta
from www.core import Synapse, Env
from www.services.synapse_space.basic import CreateBasicSpaceService
import synapseclient as syn


@pytest.fixture
def mk_service(syn_test_helper, mk_uniq_real_email, basic_config, set_basic_config):
    services = []

    def _mk(config=None,
            project_name=syn_test_helper.uniq_name(prefix='Project_'),
            team_name=syn_test_helper.uniq_name(prefix='Team_'),
            user_identifier=mk_uniq_real_email(),
            comments=syn_test_helper.uniq_name(prefix='Comment_')
            ):

        if not config:
            config = basic_config

        # Set the config in the Env so it's available to the service.
        set_basic_config([config])

        service = CreateBasicSpaceService(config['id'],
                                          project_name,
                                          user_identifier,
                                          team_name=team_name,
                                          comments=comments)
        services.append(service)
        return service

    yield _mk
    for service in services:
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


def test_it_creates_the_project(mk_service, assert_basic_service_success):
    service = mk_service()
    assert service.execute() == service
    assert_basic_service_success(service)


def test_it_does_not_create_a_duplicate_project(mk_service,
                                                assert_basic_service_errors,
                                                syn_test_helper):
    existing_project = syn_test_helper.create_project()
    service = mk_service(project_name=existing_project.name)
    assert service.execute() == service
    assert_basic_service_errors(service)

    assert service.project is None
    assert len(service.errors) == 1
    assert service.errors[0] == 'Project with name: "{0}" already exists.'.format(existing_project.name)


def test_it_sets_the_storage_location(mk_service, assert_basic_service_success, syn_client):
    service = mk_service()
    assert service.execute() == service
    assert_basic_service_success(service)

    storage_id = Env.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()
    storage_setting = syn_client.getProjectSetting(service.project.id, 'upload')
    storage_ids = storage_setting.get('locations')
    assert storage_id in storage_ids


def test_it_creates_the_team(mk_service, assert_basic_service_success):
    service = mk_service()
    assert service.execute() == service
    assert_basic_service_success(service)

    assert service.team.name == service.team_name


def test_it_assigns_the_team_to_the_project(mk_service, assert_basic_service_success, syn_client):
    service = mk_service()
    assert service.execute() == service
    assert_basic_service_success(service)

    syn_perms = syn_client.getPermissions(service.project, principalId=service.team.id)
    assert syn_perms
    syn_perms.sort() == Synapse.CAN_DOWNLOAD_PERMS.sort()


def test_it_writes_the_log_file_on_success(mk_service,
                                           assert_basic_service_success,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch):
    project = syn_test_helper.create_project()
    folder = syn_client.store(syn.Folder(name='Synapse Admin Log', parent=project))

    monkeypatch.setenv('SYNAPSE_SPACE_LOG_FOLDER_ID', folder.id)

    service = mk_service()
    assert service.project_name is not None
    assert service.team_name is not None
    assert service.comments is not None
    assert service.execute() == service
    assert_basic_service_success(service)

    files = list(Synapse.client().getChildren(folder))
    assert len(files) == 1

    file = Synapse.client().get(files[0]['id'])
    assert file.name.endswith('_basic_create_space.json')
    with open(file.path, mode='r') as f:
        jdata = json.loads(f.read())

    jparms = jdata['parameters']
    assert jparms['project_name'] == service.project_name
    assert jparms['team_name'] == service.team_name
    assert jparms['comments'] == service.comments
    assert jparms['user'] == service.user_identifier

    jproject = jdata['project']
    assert jproject['id'] == service.project.id
    assert jproject['name'] == service.project.name

    jteam = jdata['team']
    assert jteam['id'] == service.team.id
    assert jteam['name'] == service.team.name


def test_it_writes_the_log_file_on_failure(mk_service,
                                           syn_test_helper,
                                           syn_client,
                                           monkeypatch,
                                           assert_basic_service_success):
    # TODO:
    pass


###############################################################################
# Validations
###############################################################################

def test_validations_validate_project_name(syn_test_helper):
    existing_project = syn_test_helper.create_project()
    error = CreateBasicSpaceService.Validations.validate_project_name(existing_project.name)
    assert error == 'Project with name: "{0}" already exists.'.format(existing_project.name)


def test_validations_validate_team_name(syn_test_helper):
    existing_team = syn_test_helper.create_team()
    error = CreateBasicSpaceService.Validations.validate_team_name(existing_team.name)
    assert error == 'Team with name: "{0}" already exists.'.format(existing_team.name)
