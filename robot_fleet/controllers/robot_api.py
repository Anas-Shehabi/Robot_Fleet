from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)
# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
class RobotApi(http.Controller):
    @http.route("/v1/robot/update/<int:robot_id>",methods=["PUT"], type="http", auth="none", csrf=False)
    def update_robot(self, robot_id):
        """
        Updates a robot's status and location in Odoo.
        Expects JSON payload: {'name': str, 'status': str, 'location_id': int}
        Returns: {'success': bool, 'message': str}
        """
        try:
            robot_id = request.env['robot'].sudo().search([('id','=',robot_id)])
            print(robot_id)
            #Parse incoming JSON data
            args = request.httprequest.data.decode()
            vals = json.loads(args)
            #print(vals)
            _logger.info(f"{GREEN}Received data: {vals}{RESET}")
            if(robot_id):
                print(robot_id.write(vals))
                if robot_id.write(vals):
                    return request.make_json_response({
                             "success": True,
                             "message": "Robot updated successfully"},status=201)

            else:
                 return request.make_json_response({
                                "success": False,
                                "message": "Robot IDs didn't found"},status=400)
        except Exception as error:
            error_msg = f"Server error: {str(error)}"
            _logger.error(f"{CYAN}{error_msg}{RESET}")
            return request.make_json_response({
                "success": False,
                "message": error_msg},status=400)


