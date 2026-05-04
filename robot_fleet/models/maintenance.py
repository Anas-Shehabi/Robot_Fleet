# from odoo import models, fields
#
# class RobotMaintenance(models.Model):
#     _name = 'robot.maintenance'
#     _description = 'Robot Maintenance'
#
#     robot_id = fields.Many2one('robot', required=True, string='Robot',readonly=True)
#     date_start = fields.Datetime(string='Start Date', default=fields.Datetime.now,required=True)
#     date_end = fields.Datetime(string='End Date')
#     technician_id = fields.Many2one('res.users', string='Technician', default=lambda self: self.env.user)
#     description = fields.Text(string='Maintenance Description',required=True)
#     notes = fields.Text(string='Additional Notes')
#     damage_images = fields.Many2many(
#         'ir.attachment',
#         string="Damage Documentation",
#         help="Upload images of damages found during maintenance"
#     )

from odoo import models, fields, api
from datetime import timedelta

from odoo.exceptions import UserError


class RobotMaintenance(models.Model):
    """
    Robot Maintenance Log Model

    This model tracks maintenance activities performed on robots,
    including dates, technician, description, replaced parts, and condition status.
    """
    _name = 'robot.maintenance'
    _description = 'Robot Maintenance'
    _rec_name = 'ref'
    # Archiving
    active = fields.Boolean(default=True)

    # add ref to present a sequences
    ref = fields.Char(default='New', readonly=1)

    # Link to the robot being serviced
    robot_id = fields.Many2one('robot', required=True, string='Robot', readonly=True, ondelete="cascade")

    # Start and end times of maintenance
    date_start = fields.Datetime(string='Start Date',readonly=True)
    date_end = fields.Datetime(string='End Date',readonly=True)

    # Assigned technician (default is the current user)
    technician_id = fields.Many2one('res.users', string='Technician', default=lambda self: self.env.user,readonly=True)

    # Type of maintenance performed
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('calibration', 'Calibration'),
        ('software_update', 'Software Update'),
    ], string='Maintenance Type', required=True)

    maintenance_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'in Progress'),
        ('finished', 'Finished'),
    ], string='Maintenance State', required=True,default="not_started",readonly=True)

    # Description of the maintenance work
    description = fields.Text(string='Maintenance Description', required=True)

    # Optional notes for additional comments
    notes = fields.Text(string='Additional Notes')

    # Images showing damage or issues found during maintenance
    damage_images = fields.Many2many(
        'ir.attachment',
        string="Damage Documentation",
        help="Upload images of damages found during maintenance"
    )

    # Parts replaced during this maintenance (as simple text)
    replaced_parts = fields.Char(string='Replaced Parts', help="List any parts replaced during maintenance")

    # Computed field showing downtime in hours
    downtime_duration = fields.Float(string='Downtime (Hours)', compute='_compute_downtime', store=True,readonly=True)

    @api.depends('date_start', 'date_end')
    def _compute_downtime(self):
        """Computes the downtime in hours between start and end dates."""
        for record in self:
            if record.date_start and record.date_end:
                duration = record.date_end - record.date_start
                record.downtime_duration = duration.total_seconds() / 3600.0
            else:
                record.downtime_duration = 0.0

    # Optional cost tracking
    maintenance_cost = fields.Monetary(string='Maintenance Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Scheduled date for next maintenance
    next_maintenance_date = fields.Date(string='Next Scheduled Maintenance')

    # Robot's condition before maintenance
    condition_before = fields.Selection([
        ('good', 'Good'),
        ('minor_fault', 'Minor Fault'),
        ('critical', 'Critical'),
    ], string='Condition Before Maintenance')

    # Robot's condition after maintenance
    condition_after = fields.Selection([
        ('good', 'Good'),
        ('minor_fault', 'Minor Fault'),
        ('needs_followup', 'Needs Follow-Up'),
    ], string='Condition After Maintenance')

    # Button Action 1: Start Maintenance
    def action_start_maintenance(self):
        for record in self:
            if record.date_start:
                raise UserError("Maintenance has already started.")
            if record.robot_id.status_robot != 'idle':
                raise UserError("Robot must be in idle state.")
            else:
                record.date_start = fields.Datetime.now()
                record.robot_id.status_robot = 'maintenance'
                record.maintenance_state = 'in_progress'

    # Button Action 2: End Maintenance
    def action_end_maintenance(self):
        for record in self:
            record.date_end = fields.Datetime.now()
            record.robot_id.status_robot = 'idle'
            record.maintenance_state = 'finished'



    @api.model
    def create (self,vals):
        res = super(RobotMaintenance,self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('maintenance_seq')
        #print(res.ref)
        return res