# --------------------------------------------
# task.py - robot_fleet.task model
# --------------------------------------------
import requests

from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta


class Task(models.Model):
    _name = 'robot_fleet.task'
    _description = 'Robot Task'
    _inherit = ['mail.thread','mail.activity.mixin']
    #Archiving
    active = fields.Boolean(default=True)

    tags_ids = fields.Many2many('task_tag')

    # add ref to present a sequences
    ref=fields.Char(default='New',readonly=1)

    name=fields.Char(string='Task Name')
    description = fields.Text(string='Task Description', tracking=1 )
    task_begins = fields.Datetime(tracking=1)
    task_ends = fields.Datetime()

    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string='Status', default='new',tracking=1)

    robot_id = fields.Many2one('robot', string='Assigned Robot',tracking=1)
    task_owner_id = fields.Many2one('task.owner',tracking=1)

    robot_ids = fields.One2many('robot','task_id',tracking=1)

    source_station_id = fields.Many2one('station', string='Source Station',tracking=1)
    destination_station_id = fields.Many2one('station', string='Destination Station',tracking=1)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company this task belongs to"
    )

    shipment_ids = fields.One2many(
        'robot_fleet.shipment',
        'task_id',
        string='Shipment Items'
    )

    total_shipment_weight = fields.Float(
        string="Total Shipment Weight (kg)",
        compute="_compute_total_shipment_weight",
        store=True
    )


    def action_new(self):
        for rec in self:
            rec.status='new'

    def action_in_progres(self):
        for rec in self:
            if not rec.robot_ids:
                raise ValidationError("Please assign Robot/s")
            rec.status = 'in_progress'
            for robot in rec.robot_ids:
                ############################################
                if not robot.ip_address:
                    raise ValidationError(f"Robot {robot.name} has no IP address assigned.")

                payload = {
                    "task_ref": rec.ref,
                    "task_id": rec.id
                }

                url = f"http://{robot.ip_address}:5005//receive_task"
                #"http://127.0.0.1:5005/receive_task"

                try:
                    response = requests.post(url, json=payload, timeout=5)
                    if response.status_code not in (200, 201):
                        raise ValidationError(
                            f"Robot {robot.name} returned an error: {response.text}"
                        )
                except Exception as e:
                    raise ValidationError(
                        f"Could not send task to robot {robot.name}: {str(e)}"
                    )
                ###############################################
                robot.status_robot = 'active'
                robot.current_task_id = rec.id
                rec.task_begins = fields.Datetime.now()

    def action_done(self):
        for rec in self:
            rec.status = 'done'
            rec.task_ends = fields.Datetime.now()
            for robot in rec.robot_ids:
                robot.status_robot = 'idle'
                robot.current_task_id = False
                robot.completed_task_ids |= rec



    @api.model
    def create (self,vals):
        res = super(Task,self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('task_seq')
        #print(res.ref)
        return res

    """
    For each robot assigned to the task:
    It checks if status_robot == 'active'
    Then checks if robot.current_task_id.ref != task.ref (i.e., robot is active and working on a different task)
    If such robots exist, it blocks the assignment and gives their names
    """
    @api.constrains('robot_ids')
    def _check_robot_not_active(self):
        for task in self:
            active_robots = []
            for robot in task.robot_ids:
                if robot.status_robot == 'active':
                    if not robot.current_task_id or robot.current_task_id.ref != task.ref:
                        if robot.name not in active_robots:
                            active_robots.append(robot.name)
            if active_robots:
                robot_names = ', '.join(active_robots)
                raise ValidationError(f"Cannot assign active robot(s) to a task: {robot_names}")

#    @api.constrains('robot_id', 'company_id')
#    def _check_robot_company(self):
#        for task in self:
#            if task.robot_id and task.robot_id.company_id != task.company_id:
#                raise ValidationError((
#                    f"Robot {task.robot_id.name} belongs to company {task.robot_id.company_id.name} "
 #                   f"while task belongs to {task.company_id.name}. "
#                    "Please select a robot from the correct company."
#                ))

    @api.constrains('robot_ids', 'company_id')
    def _check_robot_company(self):
        """Checks if all robots in the team belong to the same company as the task."""
        for task in self:
            for robot in task.robot_ids:  # Loop through the whole team
                if robot.company_id != task.company_id:
                    raise ValidationError(
                        f"Robot {robot.name} belongs to company {robot.company_id.name} "
                        f"while task belongs to {task.company_id.name}. "
                        "Please select robots from the correct company."
                    )

    @api.depends('shipment_ids.weight', 'shipment_ids.quantity')
    def _compute_total_shipment_weight(self):
        for task in self:
            task.total_shipment_weight = sum(
                item.weight * item.quantity for item in task.shipment_ids
            )


    @api.constrains('shipment_ids', 'robot_ids')
    def _check_capacity(self):
        for task in self:
            total_weight = sum(item.weight * item.quantity for item in task.shipment_ids)
            total_capacity = sum((robot.capacity or 0) for robot in task.robot_ids)

            if total_capacity and total_weight > total_capacity:
                raise ValidationError(
                    f"Total shipment weight is {total_weight}kg, but the assigned robots "
                    f"can only carry {total_capacity}kg."
                )