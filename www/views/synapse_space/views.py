from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from server import app
from www.services import CreateSynapseSpaceService, EncryptSynapseSpaceService
from .forms import CreateSynapseSpaceForm, EncryptSynapseSpaceForm


@app.route("/synapse_space/create", methods=('GET', 'POST'))
@fresh_login_required
def create_synapse_space():
    form = CreateSynapseSpaceForm()
    errors = []
    if form.validate_on_submit():
        service = CreateSynapseSpaceService(form.project_name, form.valid_emails)
        errors = service.execute()

        if not errors:
            flash('Synapse space created successfully')
            return redirect(url_for('create_synapse_space'))

    return render_template('synapse_space/create.html', form=form, errors=errors)


@app.route("/synapse_space/encrypt", methods=('GET', 'POST'))
@fresh_login_required
def encrypt_synapse_space():
    form = EncryptSynapseSpaceForm()
    errors = []
    if form.validate_on_submit() and form.encrypt_project.data:
        service = EncryptSynapseSpaceService(form.project_id.data)
        errors = service.execute()

        if not errors:
            flash('Synapse project has been encrypted')
            return redirect(url_for('encrypt_synapse_space'))

    return render_template('synapse_space/encrypt.html', form=form, errors=errors)
