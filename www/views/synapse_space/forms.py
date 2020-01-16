from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, ValidationError

from www.services import EncryptSpaceService


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

        project, error = EncryptSpaceService.Validations.validate(field.data)

        if error:
            raise ValidationError(error)
        else:
            self.can_encrypt = True
            self.project_name = project.name
