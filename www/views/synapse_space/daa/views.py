from flask import current_app as app, request
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from www.services.synapse_space.daa import GrantAccessService
from .forms import GrantSynapseAccessForm
from ....core import Cookies


@app.route("/synapse_space/daa/grant", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_daa_grant():
    form = GrantSynapseAccessForm()
    errors = []
    user_email = Cookies.user_email_get(request)
    if form.validate_on_submit():
        service = GrantAccessService(form.team_name,
                                     form.field_institution_name.data,
                                     form.field_data_collection.data,
                                     user_email,
                                     agreement_url=form.field_agreement_url.data,
                                     emails=form.valid_emails,
                                     start_date=form.field_start_date.data,
                                     end_date=form.field_end_date.data,
                                     comments=form.field_comments.data)

        errors = service.execute().errors
        warnings = service.warnings

        if not errors:
            flash('Synapse team created successfully: {0} ({1})'.format(service.team.name, service.team.id))
            for warning in (warnings or []):
                flash('WARNING: {0}'.format(warning))
            return redirect(url_for('synapse_space_daa_grant'))

    return render_template('synapse_space/daa/grant.html',
                           user=user_email,
                           form=form,
                           errors=errors)
