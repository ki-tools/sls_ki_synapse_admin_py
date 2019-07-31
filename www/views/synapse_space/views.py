from flask import render_template, redirect, url_for, flash
from server import app
from www.services.create_synapse_space_service import CreateSynapseSpaceService
from .forms import CreateSynapseSpaceForm


@app.route("/synapse_space/create", methods=('GET', 'POST'))
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
def synapse_space_created():
    return render_template('synapse_space/create_success.html')
