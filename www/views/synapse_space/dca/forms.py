from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, URL, Optional
from www.services.synapse_space.dca import CreateSpaceService
import re


class CreateSynapseSpaceForm(FlaskForm):
    # Form Fields
    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])
    field_pi_surname = StringField('Principal Investigator Surname', validators=[DataRequired()])
    field_emails = TextAreaField('Emails to invite to the project')
    field_agreement_url = StringField('Contribution Agreement URL', validators=[URL(), Optional()])
    field_submit = SubmitField('Create')

    # Validated form data
    project_name = None
    valid_emails = []
    invalid_emails = []

    # Validation Methods
    def validate_field_institution_short_name(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_field_pi_surname(self, field):
        self.try_set_project_name()
        self.try_validate_project_name()

    def validate_field_emails(self, field):
        self.valid_emails = []
        self.invalid_emails = []

        pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

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
        short_name = self.field_institution_short_name.data
        surname = self.field_pi_surname.data

        if short_name and surname:
            self.project_name = '{0}_{1}'.format(short_name, surname)

    def try_validate_project_name(self):
        if self.project_name:
            error = CreateSpaceService.Validations.validate_project_name(self.project_name)
            if error:
                raise ValidationError(error)
