# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestStationModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Station = self.env['station']

    def test_01_create_update_delete(self):
        station = self.Station.create({
            'name': 'Main Charging Station',
            'station_type': 'charging',
            'company_id': self.env.company.id,
        })
        self.assertTrue(station.id)
        self.assertEqual(station.company_id, self.env.company)

        station.write({'name': 'Updated Name'})
        self.assertEqual(station.name, 'Updated Name')

        station_id = station.id
        station.unlink()
        self.assertFalse(self.Station.browse(station_id).exists())


class TestRobotModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Robot = self.env['robot']
        self.Station = self.env['station']
        self.Task = self.env['robot_fleet.task']
        self.RobotTag = self.env['robot_tag']

        self.station_charging = self.Station.create({
            'name': 'Charging Station A',
            'station_type': 'charging',
            'company_id': self.env.company.id,
        })
        self.no_task = self.Task.create({'name': 'No Task'})
        self.tag1 = self.RobotTag.create({'name': 'Heavy Duty', 'color': 1})

    def test_01_create_defaults(self):
        robot = self.Robot.create({
            'name': 'Robot Alpha',
            'serial_number': 'SN001',
            'robot_type': 'agv',
            'capacity': 100,
            'tags_ids': [(4, self.tag1.id)],
        })
        self.assertIn(self.tag1, robot.tags_ids)
        self.assertEqual(robot.status_robot, 'idle')
        self.assertEqual(robot.current_location_id, self.station_charging)
        self.assertEqual(robot.current_task_id, self.no_task)

    def test_02_update_and_delete(self):
        robot = self.Robot.create({
            'name': 'Robot Beta',
            'serial_number': 'SN002',
        })
        robot.write({'status_robot': 'active', 'capacity': 200})
        self.assertEqual(robot.status_robot, 'active')

        robot_id = robot.id
        robot.unlink()
        self.assertFalse(self.Robot.browse(robot_id).exists())

    def test_03_unique_serial_number(self):
        self.Robot.create({'name': 'R1', 'serial_number': 'SNUM'})
        with self.assertRaises(ValidationError):
            self.Robot.create({'name': 'R2', 'serial_number': 'SNUM'})

    def test_04_no_charging_station_default(self):
        """Test robot creation when no charging station exists."""
        self.Station.search([('station_type', '=', 'charging')]).unlink()
        robot = self.Robot.create({
            'name': 'Robot No Station',
            'serial_number': 'SN999',
        })
        self.assertFalse(robot.current_location_id, "No default charging station should be set.")


class TestTaskModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Task = self.env['robot_fleet.task']
        self.Robot = self.env['robot']
        self.Station = self.env['station']
        self.TaskTag = self.env['task_tag']

        self.source_station = self.Station.create({
            'name': 'Source Station',
            'station_type': 'storage',
            'company_id': self.env.company.id,
        })
        self.dest_station = self.Station.create({
            'name': 'Destination Station',
            'station_type': 'charging',
            'company_id': self.env.company.id,
        })
        self.robot = self.Robot.create({
            'name': 'Robot One',
            'serial_number': 'R001',
        })
        self.tag1 = self.TaskTag.create({'name': 'Urgent', 'color': 2})

    def test_01_create_and_tags(self):
        task = self.Task.create({
            'name': 'Transport Crates',
            'source_station_id': self.source_station.id,
            'destination_station_id': self.dest_station.id,
            'tags_ids': [(4, self.tag1.id)],
        })
        self.assertIn(self.tag1, task.tags_ids)

    def test_02_status_transitions(self):
        task = self.Task.create({'name': 'Move Pallets'})
        task.action_new()
        self.assertEqual(task.status, 'new')

        task.robot_ids = [(4, self.robot.id)]
        task.action_in_progres()
        self.assertEqual(task.status, 'in_progress')
        self.assertEqual(self.robot.status_robot, 'active')

        task.action_done()
        self.assertEqual(task.status, 'done')
        self.assertEqual(self.robot.status_robot, 'idle')
        self.assertIn(task, self.robot.completed_task_ids)

    def test_03_in_progress_without_robot(self):
        task = self.Task.create({'name': 'Empty Task'})
        with self.assertRaises(ValidationError):
            task.action_in_progres()

    def test_04_robot_company_constraint(self):
        other_company = self.env['res.company'].create({'name': 'Other Co'})
        robot_other = self.Robot.with_company(other_company).create({
            'name': 'Other Robot',
            'serial_number': 'R002',
        })
        task = self.Task.create({'name': 'Mismatch Test'})
        with self.assertRaises(ValidationError):
            task.write({'robot_id': robot_other.id})

    def test_05_cannot_assign_active_robot(self):
        active_task = self.Task.create({'name': 'Active Task'})
        self.robot.status_robot = 'active'
        self.robot.current_task_id = active_task
        task2 = self.Task.create({'name': 'Another Task'})
        with self.assertRaises(ValidationError):
            task2.write({'robot_ids': [(4, self.robot.id)]})

    def test_06_action_done_without_robots(self):
        """Edge case: calling action_done with no robots."""
        task = self.Task.create({'name': 'Task No Robots'})
        task.action_done()
        self.assertEqual(task.status, 'done', "Status should still be set to done even with no robots.")


class TestRobotTagModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RobotTag = self.env['robot_tag']

    def test_crud(self):
        tag = self.RobotTag.create({'name': 'Outdoor', 'color': 5})
        self.assertTrue(tag.id)
        tag.write({'name': 'Indoor'})
        self.assertEqual(tag.name, 'Indoor')
        tag_id = tag.id
        tag.unlink()
        self.assertFalse(self.RobotTag.browse(tag_id).exists())


class TestTaskTagModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.TaskTag = self.env['task_tag']

    def test_crud(self):
        tag = self.TaskTag.create({'name': 'High Priority', 'color': 9})
        self.assertTrue(tag.id)
        tag.write({'name': 'Low Priority'})
        self.assertEqual(tag.name, 'Low Priority')
        tag_id = tag.id
        tag.unlink()
        self.assertFalse(self.TaskTag.browse(tag_id).exists())


class TestTaskOwnerModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.TaskOwner = self.env['task.owner']
        self.Task = self.env['robot_fleet.task']

    def test_crud_and_relation(self):
        owner = self.TaskOwner.create({
            'name': 'John Doe',
            'phone': '123456',
            'address': '123 Street',
            'company_id': self.env.company.id,
        })
        self.assertTrue(owner.id)

        task = self.Task.create({
            'name': 'Owner Task',
            'task_owner_id': owner.id,
        })
        self.assertIn(task, owner.task_ids)

        owner.write({'phone': '999999'})
        self.assertEqual(owner.phone, '999999')

        owner_id = owner.id
        owner.unlink()
        self.assertFalse(self.TaskOwner.browse(owner_id).exists())
