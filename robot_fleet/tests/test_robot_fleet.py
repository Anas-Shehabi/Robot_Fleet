# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from odoo import fields
from odoo.tools import mute_logger # Wichtig für SQL-Constraint-Tests

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

    def test_02_station_company(self):
        """Test if the company is assigned correctly by default."""

        # 1. Wir erstellen die Station
        station = self.Station.create({
            'name': 'Meine Test-Station',
            'station_type': 'storage',
        })

        # Prüft, ob die Firma des station der Firma des aktuellen Test-Environments entspricht
        self.assertEqual(station.company_id, self.env.company)


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
            'ip_address': '127.0.0.1',
            'tags_ids': [(4, self.tag1.id)],
        })

        # Many2many
        self.assertIn(self.tag1, robot.tags_ids)
        # Default status
        self.assertEqual(robot.status_robot, 'idle')
        # Default station
        self.assertTrue(robot.current_location_id)
        self.assertEqual(robot.current_location_id.station_type, 'charging')
        # No assigned task yet
        self.assertFalse(robot.task_id)
        # Default current task = "No Task"
        self.assertTrue(robot.current_task_id)
        self.assertEqual(robot.current_task_id.name, 'No Task')

    def test_02_update_and_delete(self):
        robot = self.Robot.create({
            'name': 'Robot Beta',
            'serial_number': 'SN002',
            'robot_type': 'agv',
            'capacity': 100,
            'ip_address':'127.0.0.1',
        })
        robot.write({'status_robot': 'active', 'capacity': 200})
        self.assertEqual(robot.status_robot, 'active')
        self.assertEqual(robot.capacity, 200)
        robot_id = robot.id
        robot.unlink()
        self.assertFalse(self.Robot.browse(robot_id).exists())

    @mute_logger('odoo.sql_db')  # Unterdrückt den hässlichen roten Datenbank-Fehler im Log
    def test_03_unique_serial_number(self):
        self.Robot.create({'name': 'R1', 'serial_number': 'SNUM'})

        # SQL Constraints werfen einen Exception-Typ der Datenbank (IntegrityError / UniqueViolation)
        with self.assertRaises(Exception):
            self.Robot.create({'name': 'R2', 'serial_number': 'SNUM'})

    def test_04_no_charging_station_default(self):
        """Test robot creation when no charging station exists."""
        self.Station.search([('station_type', '=', 'charging')]).unlink()
        robot = self.Robot.create({
            'name': 'Robot No Station',
            'serial_number': 'SN999',
        })
        self.assertFalse(robot.current_location_id, "No default charging station should be set.")

    def test_05_no_task_record_default(self):
        """Test robot creation when the 'No Task' record is missing."""
        # Löscht rigoros JEDEN Datensatz mit dem Namen 'No Task' (auch den aus den XML/CSV-Daten)
        self.env['robot_fleet.task'].search([('name', '=', 'No Task')]).unlink()

        robot = self.Robot.create({
            'name': 'Robot No Task Default',
            'serial_number': 'SN888',
        })
        # Jetzt MUSS es leer sein, da wirklich kein Datensatz mehr übrig ist
        self.assertFalse(robot.current_task_id, "Should be empty if 'No Task' record doesn't exist.")

    @mute_logger('odoo.sql_db')
    def test_06_required_fields(self):
        """Test that missing required fields block the creation."""
        # Versuch ohne Name
        with self.assertRaises(Exception):
            self.Robot.create({
                'serial_number': 'SN_NO_NAME',
            })

        # Versuch ohne Seriennummer
        with self.assertRaises(Exception):
            self.Robot.create({
                'name': 'No Serial Robot',
            })

    def test_07_company_default(self):
        """Test if the company is assigned correctly by default."""
        robot = self.Robot.create({
            'name': 'Company Test Robot',
            'serial_number': 'SN_COMP',
        })
        # Prüft, ob die Firma des Roboters der Firma des aktuellen Test-Environments entspricht
        self.assertEqual(robot.company_id, self.env.company)

class TestTaskModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Task = self.env['robot_fleet.task']
        self.Robot = self.env['robot']
        self.Station = self.env['station']
        self.TaskTag = self.env['task_tag']
        self.Shipment = self.env['robot_fleet.shipment']  # WICHTIG für die Gewichtstests!

        # --- BASISDATEN FÜR ALLE TESTS ---
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
            'capacity': 100,  # WICHTIG: Kapazität für Constraint-Tests ergänzt!
        })
        self.tag1 = self.TaskTag.create({'name': 'Urgent', 'color': 2})

    def test_01_create_defaults_and_sequence(self):
        """Testet die Anlage mit realistischen Daten, Standardwerten und Sequence."""
        # Wir nutzen direkt dein tolles Setup für die Anlage!
        task = self.Task.create({
            'name': 'Transport Paletten',
            'source_station_id': self.source_station.id,
            'destination_station_id': self.dest_station.id,
            'tags_ids': [(4, self.tag1.id)],
        })

        # Standardwerte & Relationen prüfen
        self.assertEqual(task.status, 'new')
        self.assertEqual(task.company_id, self.env.company)
        self.assertEqual(task.source_station_id, self.source_station)
        self.assertIn(self.tag1, task.tags_ids)

        # Prüfen, ob die Sequenz (ref) aus 'New' umgewandelt wurde
        self.assertTrue(task.ref)
        self.assertNotEqual(task.ref, 'New', "Die Sequenz wurde nicht generiert!")

    def test_02_compute_total_shipment_weight(self):
        """Testet, ob das Gesamtgewicht der Ladung korrekt berechnet wird."""
        task = self.Task.create({'name': 'Gewicht-Test'})

        # Ladungen hinzufügen (Gewicht * Menge)
        self.Shipment.create({
            'task_id': task.id,
            'name': 'Kiste A',
            'weight': 10.5,
            'quantity': 2,  # 21.0 kg
        })
        self.Shipment.create({
            'task_id': task.id,
            'name': 'Kiste B',
            'weight': 5.0,
            'quantity': 1,  # 5.0 kg
        })

        # Erwartetes Gesamtgewicht: 21.0 + 5.0 = 26.0 kg
        self.assertEqual(task.total_shipment_weight, 26.0)

    def test_03_constraint_capacity_detailed(self):
        """Testet die Kapazitätsgrenze: 1. Erlaubtes Gewicht, 2. Überschrittenes Gewicht."""
        task = self.Task.create({'name': 'Kapazitaets-Test Detail'})
        task.write({'robot_ids': [(4, self.robot.id)]})  # robot_ids ist One2many

        # --- POSITIV-TEST (Erlaubtes Gewicht: 80kg von 100kg) ---
        # WICHTIG: Wir fügen die Ladung über task.write hinzu, damit das Task-Constraint auslöst!
        task.write({
            'shipment_ids': [(0, 0, {
                'name': 'Erlaubte Kisten',
                'weight': 40.0,
                'quantity': 2,
            })]
        })

        # Prüft die mathematische Korrektheit der Ladung am Task
        self.assertEqual(task.total_shipment_weight, 80)

        # --- NEGATIV-TEST (Überschreitung auf 110kg) ---
        # Jetzt versuchen wir, das Limit zu sprengen. Wir packen noch eine 30 kg Kiste dazu.
        with self.assertRaises(ValidationError):
            task.write({
                'shipment_ids': [(0, 0, {
                    'name': 'Zu schwere Kiste',
                    'weight': 30.0,
                    'quantity': 1,
                })]
            })

    def test_04_constraint_company_mismatch(self):
        """Testet, ob ein Roboter aus einer anderen Firma blockiert wird."""

        # Odoo-Accounting erfordert zwingend Daten zum Geschäftsjahr bei neuen Firmen
        other_company = self.env['res.company'].search([('id', '!=', self.env.company.id)], limit=1)

        # Roboter in der Fremdfirma anlegen
        robot_other = self.Robot.with_company(other_company).create({
            'name': 'Fremder Roboter',
            'serial_number': 'TSN-OTHER',
        })

        # Versuch, den fremden Roboter über das robot_ids Feld zuzuweisen
        with self.assertRaises(ValidationError):
            self.Task.create({
                'name': 'Firmen Mismatch Test',
                'robot_ids': [(4, robot_other.id)]
            })

    def test_05_constraint_active_robot(self):
        """Testet, ob einem bereits aktiven Roboter eine neue Aufgabe zugewiesen werden kann."""
        task = self.Task.create({'name': 'Aktiv-Test'})

        # Wir manipulieren den Roboter-Status manuell auf 'active', ohne die API zu triggern
        self.robot.status_robot = 'active'

        # Versuch, diesen aktiven Roboter der neuen Aufgabe zuzuweisen
        with self.assertRaises(ValidationError):
            task.write({'robot_ids': [(4, self.robot.id)]})

    def test_06_update_and_delete(self):
        """Testet das Aktualisieren (Update) und Löschen (Delete) einer Aufgabe."""
        task = self.Task.create({
            'name': 'Ursprünglicher Task',
            'description': 'Leer',
        })

        # UPDATE
        task.write({
            'name': 'Aktualisierter Task',
            'description': 'Dies ist eine neue Beschreibung',
        })
        self.assertEqual(task.name, 'Aktualisierter Task')
        self.assertEqual(task.description, 'Dies ist eine neue Beschreibung')

        # DELETE
        task_id = task.id
        task.unlink()
        self.assertFalse(self.Task.browse(task_id).exists())


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


class TestRobotMaintenanceModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Maintenance = self.env['robot.maintenance']
        self.Robot = self.env['robot']

        # Wir brauchen einen Standard-Roboter für die Wartungstests
        self.robot = self.Robot.create({
            'name': 'Wartungs-Test-Roboter',
            'serial_number': 'MNT-001',
            'status_robot': 'idle',  # Wichtig für action_start_maintenance
        })

    def test_01_create_defaults_and_sequence(self):
        """Testet die Erstellung, Standardwerte und Nummernvergabe."""
        maint = self.Maintenance.create({
            'robot_id': self.robot.id,
            'maintenance_type': 'preventive',
            'description': 'Monatliche Routineprüfung',
        })

        # Standardwerte prüfen
        self.assertTrue(maint.active)
        self.assertEqual(maint.maintenance_state, 'not_started')
        self.assertEqual(maint.technician_id, self.env.user, "Der aktuelle User sollte Techniker sein.")

        # Nummernkreis-Prüfung
        self.assertNotEqual(maint.ref, 'New', "Die Sequenz für die Wartung wurde nicht generiert!")

    def test_02_compute_downtime(self):
        """Testet die korrekte Berechnung der Ausfallzeit (Downtime) in Stunden."""
        maint = self.Maintenance.create({
            'robot_id': self.robot.id,
            'maintenance_type': 'corrective',
            'description': 'Zeit-Test',
        })

        #  simulieren einen manuellen Start- und Endzeitpunkt (exakt 2,5 Stunden Differenz)
        start_time = fields.Datetime.now()
        end_time = start_time + timedelta(hours=2, minutes=30)

        maint.write({
            'date_start': start_time,
            'date_end': end_time
        })

        # 2 Stunden und 30 Minuten = 2.5 Stunden
        self.assertEqual(maint.downtime_duration, 2.5, "Die berechnete Ausfallzeit in Stunden stimmt nicht!")

    def test_03_action_start_and_end_maintenance(self):
        """Testet den erfolgreichen Workflow (Starten und Beenden) und die Roboter-Kopplung."""
        maint = self.Maintenance.create({
            'robot_id': self.robot.id,
            'maintenance_type': 'calibration',
            'description': 'Workflow-Test',
        })

        # --- SCHRITT 1: WARTUNG STARTEN ---
        maint.action_start_maintenance()

        # Prüfen, ob die Startzeit gesetzt wurde und die Status umgeschaltet sind
        self.assertTrue(maint.date_start)
        self.assertEqual(maint.maintenance_state, 'in_progress')
        self.assertEqual(self.robot.status_robot, 'maintenance',
                         "Der Roboter-Status wurde nicht auf 'maintenance' gesetzt!")

        # --- SCHRITT 2: WARTUNG BEENDEN ---
        maint.action_end_maintenance()

        # Prüfen, ob die Endzeit gesetzt wurde und alles korrekt abgeschlossen ist
        self.assertTrue(maint.date_end)
        self.assertEqual(maint.maintenance_state, 'finished')
        self.assertEqual(self.robot.status_robot, 'idle',
                         "Der Roboter wurde nach der Wartung nicht wieder auf 'idle' gesetzt!")

    def test_04_maintenance_user_errors(self):
        """Testet, ob das System ungültige Wartungs-Starts erfolgreich abblockt."""
        maint = self.Maintenance.create({
            'robot_id': self.robot.id,
            'maintenance_type': 'software_update',
            'description': 'Fehler-Test',
        })

        # --- FEHLERFALL 1: Roboter ist nicht 'idle' ---
        # Wir manipulieren den Roboter, sodass er gerade arbeitet
        self.robot.status_robot = 'active'

        with self.assertRaises(UserError):
            maint.action_start_maintenance()

        # --- FEHLERFALL 2: Wartung wurde bereits gestartet ---
        # Wir setzen den Roboter zurück auf 'idle' und starten die Wartung regulär
        self.robot.status_robot = 'idle'
        maint.action_start_maintenance()

        # Versuch, die bereits laufende Wartung NOCHMAL zu starten
        with self.assertRaises(UserError):
            maint.action_start_maintenance()