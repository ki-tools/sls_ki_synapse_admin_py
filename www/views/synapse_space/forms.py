from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email

from www.core import ParamStore
from www.core.synapse import Synapse
import synapseclient as syn
from synapseclient.exceptions import SynapseHTTPError
import re


class CreateSynapseSpaceForm(FlaskForm):
    # Form Fields
    institution_name = StringField('Institution Name', validators=[DataRequired()])
    pi_name = StringField('PI Name', validators=[DataRequired()])
    emails = TextAreaField('Emails to add to the project', validators=[DataRequired()])
    submit = SubmitField('Create')

    # Validated form data
    project_name = None
    valid_emails = []
    invalid_emails = []

    # Validation Methods
    def validate_institution_name(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_pi_name(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_emails(self, field):
        self.valid_emails = []
        self.invalid_emails = []

        pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")

        for email in self.parse_emails(field.data):
            if not re.match(pattern, email):
                self.invalid_emails.append(email)
            else:
                self.valid_emails.append(email)

        if self.invalid_emails:
            raise ValidationError('Invalid field: {0}'.format(', '.join(self.invalid_emails)))

    # Helper Methods
    def parse_emails(self, emails):
        delimiters = ',', ';', ':', '\n', '\r\n', ' '
        pattern = '|'.join(map(re.escape, delimiters))
        return list(filter(len, re.split(pattern, emails)))

    def try_set_project_name(self):
        self.project_name = None
        if self.institution_name.data and self.pi_name.data:
            self.project_name = 'KiContributor_{0}_{1}'.format(self.institution_name, self.pi_name)

    def try_validate_project_name(self):
        if self.project_name:
            existing_project_id = Synapse.client().findEntityId(name=self.project_name)
            if existing_project_id:
                raise ValidationError('Synapse project with name: "{0}" already exists.'.format(self.project_name))


class EncryptSynapseSpaceForm(FlaskForm):
    # Form Fields
    project_id = StringField('Synapse Project ID', validators=[DataRequired()])
    check_project = SubmitField('Check Project ID')
    encrypt_project = SubmitField('Encrypt')

    # Validated form data
    can_encrypt = False
    project_name = None

    # Validation Methods
    def validate_project_id(self, field):
        self.can_encrypt = False
        self.project_name = None
        try:
            project = Synapse.client().get(syn.Project(id=field.data))
            storage_id = ParamStore.SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID()

            # Check if the project is already encrypted.
            storage_setting = Synapse.client().getProjectSetting(project, 'upload')
            if storage_setting is not None:
                storage_ids = storage_setting.get('locations')
                if storage_id in storage_ids:
                    raise ValidationError(
                        'Storage location already set for project: {0} ({1})'.format(project.name, project.id))

            self.can_encrypt = True
            self.project_name = project.name

        except SynapseHTTPError as ex:
            if ex.response.status_code == 404:
                raise ValidationError('Synapse project ID: "{0}" does not exist.'.format(field.data))
            else:
                raise ValidationError('Unknown error validating synapse project.')
