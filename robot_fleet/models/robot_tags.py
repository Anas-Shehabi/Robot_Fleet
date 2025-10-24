from odoo import models,fields

class TaskTag(models.Model):
    _name = 'robot_tag'

    name = fields.Char(string='Tag Name')
    color = fields.Integer(string='Color')