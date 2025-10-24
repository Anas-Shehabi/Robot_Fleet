from odoo import models, fields


class TaskOwner (models.Model):

    _name = 'task.owner'
    active = fields.Boolean(default=True)


    name = fields.Char(required=1)
    phone = fields.Char()
    address = fields.Char()
    task_ids = fields.One2many('robot_fleet.task','task_owner_id')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company this Owner belongs to"
    )
