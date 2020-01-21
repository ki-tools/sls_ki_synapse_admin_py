from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, URL, Optional
from ...components import MultiCheckboxField
from www.services.synapse_space.daa import GrantAccessService
from www.core import Env
import re


class GrantSynapseAccessForm(FlaskForm):
    # Form Fields
    field_institution_name = StringField('Institution Name', validators=[DataRequired()])
    field_institution_short_name = StringField('Institution Short Name', validators=[DataRequired()])

    additional_parties = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_ADDITIONAL_PARTIES()
    ap_choices = [(p['name'], p['code']) for p in additional_parties]
    field_institution_add_party = MultiCheckboxField('Institution Additional Party',
                                                     choices=ap_choices,
                                                     validators=[Optional()])

    data_collections = Env.SYNAPSE_SPACE_DAA_GRANT_ACCESS_DATA_COLLECTIONS()
    dc_choices = [(c['name'], c['name']) for c in data_collections]
    field_data_collection = SelectField('Data Collection',
                                        choices=dc_choices,
                                        validators=[DataRequired()])

    field_emails = TextAreaField('Emails to invite to the project', validators=[Optional()])
    field_agreement_url = StringField('Data Access Agreement URL', validators=[URL(), Optional()])
    field_start_date = DateField('Start Date', validators=[Optional()])
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
        add_parties = ''
        if self.field_institution_add_party.data:
            party_codes = self.field_institution_add_party.data
            party_codes.sort()
            add_parties = '_'.join(party_codes)
            add_parties = '_{0}'.format(add_parties)

        if short_name and collection_name:
            self.team_name = '{0}{1}_{2}'.format(short_name, add_parties, collection_name)

    def try_validate_team_name(self):
        if self.team_name:
            error = GrantAccessService.Validations.validate_team_name(self.team_name)
            if error:
                raise ValidationError(error)
