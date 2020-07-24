from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, URL, Optional, Length
from ...components import MultiCheckboxField
from www.services.synapse_space.dca import CreateSpaceService
from www.core import Env
import re


class CreateSynapseSpaceForm(FlaskForm):
    # Form Fields
    config = Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG() or []
    field_select_config = SelectField('Select Configuration',
                                      choices=[(c['id'], c['name']) for c in config],
                                      validators=[DataRequired()])

    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])
    # Choices are set in the view and Javascript.
    field_institution_add_party = MultiCheckboxField('Institution Additional Party',
                                                     choices=[],
                                                     validators=[Optional()])
    field_pi_surname = StringField('Principal Investigator Surname',
                                   validators=[DataRequired(), Length(max=20,
                                                                      message='Must be less than or equal to 20 characters.')])
    field_emails = TextAreaField('Emails to invite to the project')
    field_agreement_url = StringField('Contribution Agreement URL', validators=[URL(), Optional()])
    field_start_date = DateField('Start Date', validators=[Optional()])
    field_end_date = DateField('End Date', validators=[Optional()])
    field_comments = TextAreaField('Comments', validators=[Optional()])
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

        add_parties = ''
        if self.field_institution_add_party.data:
            party_codes = self.field_institution_add_party.data
            party_codes.sort()
            add_parties = '_'.join(party_codes)
            add_parties = '{0}_'.format(add_parties)

        if short_name and surname:
            short_name = short_name.strip()
            self.project_name = '{0}{1}_{2}'.format(add_parties, short_name, surname)

            # Clean up the name
            # Remove multiple spaces:
            self.project_name = ' '.join(self.project_name.split()).strip()
            # Remove specific characters:
            for replace_char in ['.']:
                self.project_name = self.project_name.replace(replace_char, '')
            # Replace specific characters with underscores:
            for replace_char in [' ', '-']:
                self.project_name = self.project_name.replace(replace_char, '_')

    def try_validate_project_name(self):
        if self.project_name:
            error = CreateSpaceService.Validations.validate_project_name(self.project_name)
            if error:
                raise ValidationError(error)
