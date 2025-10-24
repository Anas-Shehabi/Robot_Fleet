from odoo import models, fields

class Station(models.Model):
    _name = 'station'
    _description = 'Robot Station'
    active = fields.Boolean(default=True)

    # Company relationship
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    name = fields.Char(string='Station Name', required=True)

    station_type = fields.Selection([
        ('laboratory', 'Laboratory'),
        ('storage', 'Storage'),
        ('charging', 'Charging Station'),
        ('assembly', 'Assembly Station'),
        ('maintenance', 'Maintenance Bay'),
        ('shipping', 'Shipping Dock')
    ], string='Station Type')