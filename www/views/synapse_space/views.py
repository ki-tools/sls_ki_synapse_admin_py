from flask import current_app as app, request
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from www.services import EncryptSpaceService
from .forms import EncryptSynapseSpaceForm
from ...core import Cookies


@app.route("/synapse_space/encrypt", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_encrypt():
    form = EncryptSynapseSpaceForm()
    errors = []
    if form.validate_on_submit() and form.field_submit.data:
        service = EncryptSpaceService(form.field_project_id.data)
        errors = service.execute().errors

        if not errors:
            flash('Synapse project {0} has been encrypted.'.format(service.project_id))
            return redirect(url_for('synapse_space_encrypt'))

    return render_template('synapse_space/encrypt.html',
                           user=Cookies.user_email_get(request),
                           form=form,
                           errors=errors)
