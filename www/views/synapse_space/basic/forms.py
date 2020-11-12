from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Optional
from www.services.synapse_space.basic import CreateBasicSpaceService


class CreateBasicSynapseSpaceForm(FlaskForm):
    # Form Fields
    field_project_name = StringField('Project Name', validators=[DataRequired()])
    field_team_name = StringField('Team Name', validators=[Optional()])
    field_comments = TextAreaField('Comments', validators=[Optional()])
    field_submit = SubmitField('Create')

    # Validation Methods
    def validate_field_project_name(self, field):
        if field.data:
            error = CreateBasicSpaceService.Validations.validate_project_name(field.data)
            if error:
                raise ValidationError(error)

    def validate_field_team_name(self, field):
        if field.data:
            error = CreateBasicSpaceService.Validations.validate_team_name(field.data)
            if error:
                raise ValidationError(error)
