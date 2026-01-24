
import unittest

from trajpy_ui.ui import load_trajectories_from_uploads, normalize_upload_event


class MockFile:
    """Mock NiceGUI file object"""

    def __init__(self, name, content):
        self.name = name
        self._data = content


class MockUploadEvent:
    """Mock NiceGUI upload event"""

    def __init__(self, file):
        self.file = file


class TestUIComponents(unittest.TestCase):

    def test_normalize_upload_event_single_file(self):
        """Test normalizing a single file upload event"""
        content = b"x,y\n0,0\n1,1\n2,4\n"
        mock_file = MockFile('test.csv', content)
        mock_event = MockUploadEvent(mock_file)

        result = normalize_upload_event(mock_event)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'test.csv')
        self.assertEqual(result[0][1], content)

    def test_normalize_upload_event_multiple_files(self):
        """Test normalizing multiple file uploads"""
        content1 = b"x,y\n0,0\n1,1\n"
        content2 = b"x,y\n2,2\n3,3\n"

        class MockMultipleEvent:
            def __init__(self):
                self.files = [
                    MockFile('test1.csv', content1),
                    MockFile('test2.csv', content2)
                ]

        mock_event = MockMultipleEvent()
        result = normalize_upload_event(mock_event)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], 'test1.csv')
        self.assertEqual(result[1][0], 'test2.csv')

    def test_load_trajectories_from_csv(self):
        """Test loading trajectories from CSV content"""
        csv_content = b"x,y\n0,0\n1,1\n2,4\n3,9\n4,16\n"
        uploads = [('test.csv', csv_content)]

        trajectories = load_trajectories_from_uploads(uploads)

        self.assertEqual(len(trajectories), 1)
        self.assertIsNotNone(trajectories[0]._r)
        self.assertEqual(len(trajectories[0]._r), 5)

    def test_load_trajectories_multiple_csv(self):
        """Test loading multiple CSV files"""
        csv1 = b"x,y\n0,0\n1,1\n2,2\n"
        csv2 = b"x,y\n5,5\n6,6\n7,7\n"
        uploads = [('file1.csv', csv1), ('file2.csv', csv2)]

        trajectories = load_trajectories_from_uploads(uploads)

        self.assertEqual(len(trajectories), 2)

    def test_load_trajectories_empty_list(self):
        """Test loading with no files"""
        trajectories = load_trajectories_from_uploads([])

        self.assertEqual(len(trajectories), 0)


if __name__ == '__main__':
    unittest.main()
