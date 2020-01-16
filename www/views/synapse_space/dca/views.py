from flask import current_app as app, request
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required, current_user
from www.services.synapse_space.dca import CreateSpaceService
from .forms import CreateSynapseSpaceForm
from ....core import Cookies


@app.route("/synapse_space/dca/create", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_dca_create():
    form = CreateSynapseSpaceForm()
    errors = []
    if form.validate_on_submit():
        service = CreateSpaceService(form.project_name,
                                     form.field_institution_name.data,
                                     current_user.id,
                                     agreement_url=form.field_agreement_url.data,
                                     emails=form.valid_emails)

        errors = service.execute().errors
        warnings = service.warnings

        if not errors:
            flash('Synapse project created successfully: {0} ({1})'.format(service.project.name, service.project.id))
            for warning in (warnings or []):
                flash('WARNING: {0}'.format(warning))
            return redirect(url_for('synapse_space_dca_create'))

    return render_template('synapse_space/dca/create.html',
                           user=Cookies.user_email_get(request),
                           form=form,
                           errors=errors)
