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

# This file is part of Zenodo.
# Copyright (C) 2012, 2013 CERN.
##
# Zenodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Zenodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with Zenodo. If not, see <http://www.gnu.org/licenses/>.
##
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""
Button that when clicked will reserve a DOI.
"""

from wtforms import Field
from lw_daap.modules.invenio_deposit.field_base import WebDepositField
from lw_daap.modules.invenio_deposit.processor_utils import replace_field_data
from lw_daap.modules.invenio_deposit.field_widgets import ButtonWidget


__all__ = ['ReserveDOIField']


def reserve_doi(dummy_form, field, submit=False, fields=None):
    if field.data is True:
        # Button was pressed
        if not field.object_data:
            # Call the user supplied function to create a doi.
            field.data = field.doi_creator()
        else:
            field.data = field.object_data
    else:
        # Button not pressed so prevent updating of DOI field (the
        # next post processor)
        raise StopIteration


class ReserveDOIField(WebDepositField, Field):
    widget = ButtonWidget(icon='icon-barcode')

    def __init__(self, doi_field=None, doi_creator=None, **kwargs):
        self.doi_field = doi_field
        self.doi_creator = doi_creator
        defaults = dict(
            icon=None,
            processors=[
                reserve_doi,
                replace_field_data(
                    self.doi_field,
                    getter=lambda f: f.data['doi'] if isinstance(f.data, dict)
                    else f.data
                ),
            ],
        )
        defaults.update(kwargs)
        super(ReserveDOIField, self).__init__(**defaults)

    def _value(self):
        """
        Return true if button was pressed at some point
        """
        return bool(self.data)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] is True:
            # Button was pressed
            self.data = True
        else:
            # Reset data tp value of object data.
            self.data = self.object_data
