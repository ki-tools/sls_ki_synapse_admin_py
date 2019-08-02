from flask import render_template, redirect, url_for, flash
from flask_login import login_required, fresh_login_required
from server import app
from www.services.create_synapse_space_service import CreateSynapseSpaceService
from .forms import CreateSynapseSpaceForm


@app.route("/synapse_space/create", methods=('GET', 'POST'))
@fresh_login_required
def create_synapse_space():
    form = CreateSynapseSpaceForm()
    if form.validate_on_submit():
        service = CreateSynapseSpaceService(form.project_name, form.valid_emails)
        errors = service.execute()

        if errors:
            for error in errors:
                flash(error)
        else:
            return redirect(url_for('synapse_space_created'))

    return render_template('synapse_space/create.html', form=form)


@app.route('/synapse_space/create_success')
@login_required
def synapse_space_created():
    return render_template('synapse_space/create_success.html')
