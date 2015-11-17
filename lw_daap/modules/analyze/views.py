# -*- coding: utf-8 -*-
#
# This file is part of Lifewatch DAAP.
# Copyright (C) 2015 Ana Yaiza Rodriguez Marrero.
#
# Lifewatch DAAP is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lifewatch DAAP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lifewatch DAAP. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import json

from flask import Blueprint, current_app, render_template, \
    request, redirect, url_for

from flask_menu import register_menu

from flask import Response, jsonify, flash

from invenio.ext.principal import permission_required
from invenio.modules.access.control import acc_add_action, acc_get_action_id

from lw_daap.modules.profile.decorators import delegation_required
from lw_daap.modules.profile.models import UserProfile

from . import infra
from .forms import LaunchForm, LaunchFormData
from .utils import get_requirements


blueprint = Blueprint(
    'lwdaap_analyze',
    __name__,
    url_prefix='/analyze',
    template_folder='templates',
    static_folder='static',
)


INFRA_ACCESS = 'infraaccess'


@blueprint.before_app_first_request
def create_infra_action_roles():
    """Creates the infraaccess action in the DB"""
    action_id = acc_get_action_id(INFRA_ACCESS)
    if action_id == 0:
        acc_add_action(INFRA_ACCESS, "Access to the infrastructure", "no")


@blueprint.route('/')
@register_menu(blueprint, 'main.analyze', 'Analyze', order=4)
@permission_required(INFRA_ACCESS)
def index():
    profile = UserProfile.get_or_create()
    ctx = {}
    try:
        client = infra.get_client(profile.user_proxy)
        ctx['vms'] = infra.list_vms(client)
    except infra.InfraException as e:
        flash(e.message, 'error')
    return render_template('analyze/index.html', **ctx)


@blueprint.route('/launch', methods=['GET', 'POST'])
@permission_required(INFRA_ACCESS)
def launch():
    profile = UserProfile.get_or_create()
    reqs = get_requirements()
    obj = LaunchFormData(reqs, **request.args)
    form = LaunchForm(obj=obj, user_profile=profile)
    form.fill_fields_choices(reqs)

    if form.validate_on_submit():
        client = infra.get_client(profile.user_proxy)
        image = reqs['images'][form.image.data]['image-id']
        flavor = reqs['flavors'][form.flavor.data]['flavor-id']
        app_env = reqs['app_envs'][form.app_env.data]['app-id']
        current_app.logger.debug("%s %s %s", image, flavor, app_env)
        try:
            infra.launch_vm(client,
                            name=form.name.data,
                            image=image,
                            flavor=flavor,
                            app_env=app_env,
                            recid=form.recid.data,
                            ssh_key=profile.ssh_public_key)
            return redirect(url_for('.index'))
        except infra.InfraException as e:
            flash(e.message, 'error')

    ctx = dict(
        form=form,
        flavors=reqs['flavors'],
    )
    return render_template('analyze/launch.html', **ctx)


@blueprint.route('/terminate/<vm_id>', methods=['POST'])
@permission_required(INFRA_ACCESS)
def terminate(vm_id):
    profile = UserProfile.get_or_create()
    client = infra.get_client(profile.user_proxy)
    infra.terminate_vm(client, vm_id)
    return redirect(url_for('.index'))


@blueprint.route('/connect/<vm_id>', methods=['GET'])
@permission_required(INFRA_ACCESS)
def connect(vm_id):
    profile = UserProfile.get_or_create()
    client = infra.get_client(profile.user_proxy)
    return jsonify(infra.get_vm_connection(client, vm_id))
