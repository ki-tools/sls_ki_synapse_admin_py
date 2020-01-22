from flask import current_app as app, request
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from www.services.synapse_space.dca import CreateSpaceService
from .forms import CreateSynapseSpaceForm
from ....core import Cookies


@app.route("/synapse_space/dca/create", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_dca_create():
    form = CreateSynapseSpaceForm()
    errors = []
    user_email = Cookies.user_email_get(request)
    if form.validate_on_submit():
        service = CreateSpaceService(form.project_name,
                                     form.field_institution_name.data,
                                     user_email,
                                     agreement_url=form.field_agreement_url.data,
                                     emails=form.valid_emails,
                                     start_date=form.field_start_date.data,
                                     end_date=form.field_end_date.data,
                                     comments=form.field_comments.data)

        errors = service.execute().errors
        warnings = service.warnings

        if not errors:
            flash('Synapse project created successfully: {0} ({1})'.format(service.project.name, service.project.id))
            for warning in (warnings or []):
                flash('WARNING: {0}'.format(warning))
            return redirect(url_for('synapse_space_dca_create'))

    return render_template('synapse_space/dca/create.html',
                           user=user_email,
                           form=form,
                           errors=errors)
