def add_no_task_record(env):
    task = env['robot_fleet.task']
    print("🚀 pre_init_hook called")
    if not task.search([('name', '=', 'No Task')]):
        task.create({
            'name': 'No Task',
            'status': 'new',
            'description': 'Default task when no task is assigned',
        })

