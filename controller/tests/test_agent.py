import unittest

from controller import AgentVolumesEntry

import akiri.framework.sqlalchemy as meta

class AgentTest(unittest.TestCase):

    def setUp(self):
        self.engine = meta.create_engine('sqlite://', echo=False)
        self.session = meta.Session()

    def tearDown(self):
        meta.sqa.dispose_session()
        meta.sqa.engine.dispose()
        meta.sqa.engine = None

    def test_has_available_space(self):
        # Prepare data
        c_entry = AgentVolumesEntry(volid=15, agentid=10, size=350000, available_space=320000,
                                    archive_limit=150000, archive=True, active=True,
                                    vol_type="Fixed", priority=50)
        self.session.add(c_entry)
        d_entry = AgentVolumesEntry(volid=16, agentid=10, size=15000, available_space=10000,
                                    archive_limit=15000, archive=True, active=True,
                                    vol_type="Fixed", priority=100)
        self.session.add(d_entry)

        # Perform the tests
        # When more than one volume is good, choose one with higher priority
        volume = AgentVolumesEntry.has_available_space(10, 1000)
        self.assertEqual(volume.volid, 16)

        # Choose the smaller priority one if only that one matches all the criteria
        volume = AgentVolumesEntry.has_available_space(10, 90000)
        self.assertEqual(volume.volid, 15)

    def test_has_available_space_no_volumes(self):
        volume = AgentVolumesEntry.has_available_space(10, 1000)
        self.assertIsNone(volume)
