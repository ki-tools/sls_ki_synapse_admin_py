from flask import current_app as app, request, jsonify
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from www.services.synapse_space.dca import CreateDcaSpaceService
from .forms import CreateDcaSynapseSpaceForm
from ....core import Cookies, Env


@app.route("/synapse_space/dca/create", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_dca_create():
    form = CreateDcaSynapseSpaceForm()
    errors = []
    user_email = Cookies.user_email_get(request)

    if request.method == 'POST':
        config_id = form.field_select_config.data
    else:
        config_id = Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG()[0]['id']

    add_parties = [(c['code'], c['name']) for c in
                   Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG_by_id(config_id).get('additional_parties', [])]

    form.field_institution_add_party.choices = add_parties

    if form.validate_on_submit():
        service = CreateDcaSpaceService(form.field_select_config.data,
                                        form.project_name,
                                        form.field_institution_name.data,
                                        form.field_institution_short_name.data,
                                        user_email,
                                        agreement_url=form.field_agreement_url.data,
                                        emails=form.valid_emails,
                                        start_date=form.field_start_date.data,
                                        end_date=form.field_end_date.data,
                                        comments=form.field_comments.data)

        errors = service.execute().errors

        if not errors:
            flash('Synapse project created successfully: {0} ({1})'.format(service.project.name, service.project.id))
            return redirect(url_for('synapse_space_dca_create'))

    return render_template('synapse_space/dca/create.html',
                           user=user_email,
                           form=form,
                           errors=errors)


@app.route("/synapse_space/dca/create/additional_parties/<config_id>")
@fresh_login_required
def additional_parties(config_id):
    config = Env.SYNAPSE_SPACE_DCA_CREATE_CONFIG_by_id(config_id)
    return jsonify(config.get('additional_parties', []))
