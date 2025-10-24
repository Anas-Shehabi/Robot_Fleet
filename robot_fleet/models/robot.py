from email.policy import default

from odoo import models,fields,api

class Robot(models.Model):
    _name = 'robot'
    _description = 'Robot Fleet'

    name = fields.Char(string='Robot Name', required=True)
    serial_number = fields.Char(string='Serial Number', required=True, copy=False, index=True)


    active = fields.Boolean(default=True)
    tags_ids = fields.Many2many('robot_tag')

    robot_type = fields.Selection([
        ('agv', 'AGV'),
        ('arm', 'Arm Robot'),
        ('humanoid', 'Humanoid'),
        ('drone', 'Drone')
    ], string='Type')

    status_robot = fields.Selection([
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('maintenance', 'Maintenance')
    ], string='Status', default='idle')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    capacity = fields.Integer(string='Capacity (kg)')

    def _default_charging_station(self):
        # Find the first station with type 'charging' and return its ID
        charging_station = self.env['station'].search([('station_type', '=', 'charging')], limit=1)
        return charging_station.id if charging_station else False
    current_location_id = fields.Many2one(
        'station',
        string='Current Location',
        default=_default_charging_station
    )

    # id to the task is now related to the robot
    task_id= fields.Many2one('robot_fleet.task', string='Assigned Task')


    # One2many relation to fetch tasks assigned to this robot
    task_ids = fields.One2many('robot_fleet.task', 'robot_id', string='All Tasks')


    def _default_current_task(self):
        """Find the 'No Task' record and set it as default."""
        no_task = self.env['robot_fleet.task'].search([('name', '=', 'No Task')], limit=1)
        return no_task.id if no_task else False

    current_task_id = fields.Many2one(
        'robot_fleet.task',
        string='Current Task',
        default=_default_current_task,  # Automatically sets 'No Task'

    )

    # History of all completed tasks for this robot
    completed_task_ids = fields.Many2many('robot_fleet.task', string='Completed Tasks')

    _sql_constraints = [
        ('unique_serial_number', 'unique(serial_number)', 'The Serial Number must be unique!')
    ]



