from odoo import models, fields

class Shipment(models.Model):
    _name = 'robot_fleet.shipment'
    _description = 'Shipment Item'

    name = fields.Char(string='Item Name', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    weight = fields.Float(string='Weight (kg)')

    task_id = fields.Many2one('robot_fleet.task', string='Task', ondelete='cascade')
