

{
    'name' : "Robot Fleet",
    'author' : "Anas Shehabi",
    'category' : 'Delivery',
    'version' : '17.0.0.1.0',

    'depends' : ['base','mail',
                ],
    'data' : [
        # 1. SECURITY (GROUPS -> ACCESS RULES)
        'security/security.xml',           # Defines res.groups (like group_manager)
        'security/ir.model.access.csv',    # References res.groups

        # 2. DATA (Must be loaded early)
        'data/station.csv',
        'data/robot.csv',
        'data/sequence.xml',

        # 3. VIEWS AND ACTIONS (Views often contain the necessary <record> for the action)
        'views/base_menu.xml',  # BASE MENU (The most dependent file, as it references all the actions above)
        'views/maintenance.xml',  # MUST define action_robot_maintenance_tree
        'views/robot_view.xml',            # MUST define action_robot_fleet
        'views/station_view.xml',          # MUST define action_station_fleet
        'views/task_view.xml',             # MUST define any actions it uses (e.g., action_robot_task)
        'views/owner.xml',
        'views/task_tag_view.xml',
        'views/robot_tag_view.xml',
        # 5. REPORTS (Often depend on models/views/actions)
        'Report/maintenance.xml',
        'Report/task_report.xml'
    ],
    'test': [
        'tests/test_robot_fleet.py',
    ],
    'assets' :{
      'web.assets_backend' :  ['robot_fleet/static/src/css/task_kanban.css',
                               'robot_fleet/static/src/js/kanban_disable_drag.js',]
    },

    'application': True,
    'post_init_hook': 'add_no_task_record',  # Matches function name in hooks.py
}