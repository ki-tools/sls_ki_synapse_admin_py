from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, ValidationError, URL, Optional
from www.services.synapse_space.daa import GrantAccessService
from www.core import Env
import re


class GrantSynapseAccessForm(FlaskForm):
    # Form Fields
    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])

    data_collections = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_DATA_COLLECTIONS()
    dc_choices = [(c['name'], c['name']) for c in data_collections]
    field_data_collection = SelectField('Data Collection', choices=dc_choices, validators=[DataRequired()])
    field_emails = TextAreaField('Emails to invite to the project')
    field_agreement_url = StringField('Data Access Agreement URL', validators=[URL(), Optional()])
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

        if short_name and collection_name:
            self.team_name = '{0}_{1}'.format(short_name, collection_name)

    def try_validate_team_name(self):
        if self.team_name:
            error = GrantAccessService.Validations.validate_team_name(self.team_name)
            if error:
                raise ValidationError(error)
