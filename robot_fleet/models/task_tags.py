from odoo import models,fields

class TaskTag(models.Model):
    _name = 'task_tag'

    name = fields.Char(string='Tag Name')
    color = fields.Integer(string='Color')