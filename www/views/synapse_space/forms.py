from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, ValidationError
import re

from www.services import EncryptSynapseSpaceService, CreateSynapseSpaceService


class CreateSynapseSpaceForm(FlaskForm):
    # Form Fields
    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])
    field_pi_name = StringField('Principal Investigator Name', validators=[DataRequired()])
    field_emails = TextAreaField('Emails to add to the project')
    field_submit = SubmitField('Create')

    # Validated form data
    project_name = None
    valid_emails = []
    invalid_emails = []

    # Validation Methods
    def validate_field_institution_short_name(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_field_pi_name(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_field_emails(self, field):
        self.valid_emails = []
        self.invalid_emails = []

        pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")

        for email in self.parse_emails(field.data):
            if not re.match(pattern, email):
                self.invalid_emails.append(email)
            else:
                self.valid_emails.append(email)

        if self.invalid_emails:
            raise ValidationError('Invalid emails: {0}'.format(', '.join(self.invalid_emails)))

    # Helper Methods
    def parse_emails(self, emails):
        delimiters = ',', ';', ':', '\n', '\r\n', ' '
        pattern = '|'.join(map(re.escape, delimiters))
        return list(filter(len, re.split(pattern, emails)))

    def try_set_project_name(self):
        self.project_name = None
        if self.field_institution_short_name.data and self.field_pi_name.data:
            self.project_name = 'KiContributor_{0}_{1}'.format(self.field_institution_short_name.data,
                                                               self.field_pi_name.data)

    def try_validate_project_name(self):
        if self.project_name:
            error = CreateSynapseSpaceService.Validations.validate_project_name(self.project_name)
            if error:
                raise ValidationError(error)


class EncryptSynapseSpaceForm(FlaskForm):
    # Form Fields
    field_project_id = StringField('Synapse Project ID', validators=[DataRequired()])
    field_check_project = SubmitField('Check Project ID')
    field_submit = SubmitField('Encrypt')

    # Validated form data
    can_encrypt = False
    project_name = None

    # Validation Methods
    def validate_field_project_id(self, field):
        self.can_encrypt = False
        self.project_name = None

        project, error = EncryptSynapseSpaceService.Validations.validate(field.data)

        if error:
            raise ValidationError(error)
        else:
            self.can_encrypt = True
            self.project_name = project.name
