

from odoo import http
from odoo.addons.test_convert.tests.test_env import field
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class RobotAPIController(http.Controller):

    @http.route('/api/robot/update', auth='public', type='json', methods=['POST'], csrf=False)
    def update_robot(self, **kwargs):
        """
        Updates a robot's status and location in Odoo.
        Expects JSON payload: {'name': str, 'status': str, 'location_id': int}
        Returns: {'success': bool, 'message': str}
        """
        try:
            # 1. Parse incoming JSON data
            data = json.loads(request.httprequest.data)
            _logger.info("Received data: %s", data)  # Log raw input

            # 2. Extract required fields
            robot_name = data.get('name')
            status = data.get('status')
            location_id = data.get('location_id')
            task_ref=data.get('task_ref')
            task_status= data.get('task_status')



            # 3. Validate required fields
            if not all([robot_name, status, location_id]):
                error_msg = "Missing required fields (name, status, location_id)"
                _logger.warning(error_msg)
                return {"success": False, "message": error_msg}

            if not all([task_ref,task_status]):
                error_msg = "Missing required fields (task_ref, task_status)"
                _logger.warning(error_msg)
                return {"success": False, "message": error_msg}

            # 4. Find the robot in Odoo
            Robot = request.env['robot'].sudo()  # sudo() = admin access
            robot = Robot.search([('name', '=', robot_name)], limit=1)

            Task = request.env['robot_fleet.task'].sudo()  # sudo() = admin access
            task = Task.search([('ref', '=', task_ref)], limit=1)


            if not robot:
                error_msg = f"Robot '{robot_name}' not found"
                _logger.warning(error_msg)
                return {"success": False, "message": error_msg}

            if not task:
                error_msg = f"Task '{task_ref}' not found"
                _logger.warning(error_msg)
                return {"success": False, "message": error_msg}

            # 5. Update robot status & location
            robot.write({
                'status_robot': status,
                'current_location_id': location_id
            })
            # 5. Update Task status

            if task:
                task.write({
                    'status':task_status
                })

                if task_status =='new ':
                    task.action_new()
                elif task_status =='in_progress':
                    task.action_in_progres()
                else:
                    task.action_done()

            # 6. Log success and return response
            _logger.info("Updated robot %s (Status: %s, Location: %s)",
                        robot_name, status, location_id)
            return {"success": True, "message": "Robot updated successfully"}

            # 6. Log success and return response
            _logger.info("Updated task %s (Status: %s)",
                         task_ref, task_status)
            return {"success": True, "message": "Task updated successfully"}

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON data: {str(e)}"
            _logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            _logger.error(error_msg)
            return {"success": False, "message": error_msg}