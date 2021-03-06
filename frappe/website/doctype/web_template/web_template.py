# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import os
from shutil import rmtree

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.modules.export_file import (
	export_to_files,
	get_module_path,
	scrub_dt_dn,
)


class WebTemplate(Document):
	def validate(self):
		if self.standard and not (frappe.conf.developer_mode or frappe.flags.in_patch):
			frappe.throw(_("Enable developer mode to create a standard Web Template"))

		for field in self.fields:
			if not field.fieldname:
				field.fieldname = frappe.scrub(field.label)

		if self.standard and not self.module:
			frappe.throw(_("Please select which module this Web Template belongs to."))

	def on_update(self):
		if frappe.conf.developer_mode:
			# custom to standard
			if self.standard:
				export_to_files(record_list=[["Web Template", self.name]], create_init=True)
				self.create_template_file()

			# standard to custom
			was_standard = (self.get_doc_before_save() or {}).get("standard")
			if was_standard and not self.standard:
				self.template = self.get_template(standard=True)
				rmtree(self.get_template_folder())

	def create_template_file(self):
		"""Touch a HTML file for the Web Template and add existing content, if any."""
		if self.standard:
			path = self.get_template_path()
			if not os.path.exists(path):
				with open(path, "w") as template_file:
					if self.template:
						template_file.write(self.template)

	def get_template_folder(self):
		"""Return the absolute path to the template's folder."""
		module = self.module or "Website"
		module_path = get_module_path(module)
		doctype, docname = scrub_dt_dn(self.doctype, self.name)

		return os.path.join(module_path, doctype, docname)

	def get_template_path(self):
		"""Return the absolute path to the template's HTML file."""
		folder = self.get_template_folder()
		file_name = frappe.scrub(self.name) + ".html"

		return os.path.join(folder, file_name)

	def get_template(self, standard=False):
		"""Get the jinja template string.

		Params:
		standard - if True, look on the disk instead of in the database.
		"""
		if standard:
			template = self.get_template_path()
			with open(template, "r") as template_file:
				template = template_file.read()
		else:
			template = self.template

		return template

	def render(self, values="{}"):
		values = frappe.parse_json(values)
		values.update({"values": values})
		template = self.get_template(self.standard)

		return frappe.render_template(template, values)
