from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, URL, Optional

from www.core import Env
from ...components import MultiCheckboxField
from www.services.synapse_space.daa import GrantAccessService
import re


class GrantSynapseAccessForm(FlaskForm):
    # Form Fields
    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])

    # Choices are setup in the view.
    field_institution_add_party = MultiCheckboxField('Institution Additional Party', validators=[Optional()])
    field_data_collection = SelectField('Data Collection', validators=[DataRequired()])

    field_emails = TextAreaField('Emails to invite to the project', validators=[Optional()])
    field_agreement_url = StringField('Data Access Agreement URL', validators=[URL(), Optional()])
    field_start_date = DateField('Start Date', validators=[Optional()])
    field_end_date = DateField('End Date', validators=[Optional()])
    field_comments = TextAreaField('Comments', validators=[Optional()])
    field_submit = SubmitField('Grant Access')

    # Validated form data
    team_name = None
    valid_emails = []
    invalid_emails = []

    # Validation Methods
    def validate_field_institution_short_name(self, field):
        self.try_set_team_name()
        self.try_validate_team_name()

    def validate_field_data_collection(self, field):
        self.try_set_team_name()
        self.try_validate_team_name()

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

    def try_set_team_name(self):
        self.team_name = None
        short_name = self.field_institution_short_name.data
        collection_name = self.field_data_collection.data
        config = Env.get_default_daa_grant_access_config()
        data_collection = Env.get_daa_grant_access_data_collection_by_name(config, collection_name)

        add_parties = ''
        if self.field_institution_add_party.data:
            party_codes = self.field_institution_add_party.data
            party_codes.sort()
            add_parties = '_'.join(party_codes)
            add_parties = '{0}'.format(add_parties)

        if short_name and collection_name:
            short_name = short_name.strip()

            if data_collection['include_collection_name_in_team_name'] is True:
                if add_parties:
                    add_parties = '_' + add_parties
                self.team_name = 'KiAccess_{0}{1}_{2}'.format(collection_name, add_parties, short_name)
            else:
                if add_parties:
                    add_parties = add_parties + '_'
                self.team_name = 'KiAccess_{0}{1}'.format(add_parties, short_name)

            # Clean up the name
            # Remove multiple spaces:
            self.team_name = ' '.join(self.team_name.split()).strip()
            # Remove specific characters:
            for replace_char in ['.']:
                self.team_name = self.team_name.replace(replace_char, '')
            # Replace specific characters with underscores:
            for replace_char in [' ', '-']:
                self.team_name = self.team_name.replace(replace_char, '_')

    def try_validate_team_name(self):
        if self.team_name:
            error = GrantAccessService.Validations.validate_team_name(self.team_name)
            if error:
                raise ValidationError(error)
