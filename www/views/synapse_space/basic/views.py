from flask import current_app as app, request, jsonify
from flask import render_template, redirect, url_for, flash
from flask_login import fresh_login_required
from www.services.synapse_space.basic import CreateBasicSpaceService
from .forms import CreateBasicSynapseSpaceForm
from ....core import Cookies, Env


@app.route("/synapse_space/basic/create", methods=('GET', 'POST'))
@fresh_login_required
def synapse_space_basic_create():
    form = CreateBasicSynapseSpaceForm()
    errors = []
    user_email = Cookies.user_email_get(request)

    config = Env.get_default_basic_create_config()

    if form.validate_on_submit():
        service = CreateBasicSpaceService(config['id'],
                                          form.field_project_name.data,
                                          user_email,
                                          team_name=form.field_team_name.data,
                                          comments=form.field_comments.data)

        errors = service.execute().errors

        if not errors:
            flash('Synapse project created successfully: {0} ({1})'.format(service.project.name, service.project.id))
            return redirect(url_for('synapse_space_basic_create'))

    return render_template('synapse_space/basic/create.html',
                           user=user_email,
                           form=form,
                           errors=errors)
