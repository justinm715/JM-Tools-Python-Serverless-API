import pytest
import os
from api.region_tribs import app as flask_app
from tools.region_tribs_tools import AnnotationsExtractor, AreaAnalysisReport, AreaElementAnalyzer
from flask_testing import TestCase


# ========= Routes


class TestApp(TestCase):
    def create_app(self):
        flask_app.config['TESTING'] = True
        return flask_app

    def test_time(self):
        response = self.client.get('/api/region_tribs/time')
        assert response.status_code == 200
        assert "time" in response.json


class TestPDFUpload(TestCase):
    def create_app(self):
        flask_app.config['TESTING'] = True
        return flask_app

    def test_pdf_upload(self):
        # Path to your sample PDF file
        pdf_path = os.path.join(os.path.dirname(
            __file__), 'assets', 'test_region_tribs.pdf')

        # Open the file in binary mode
        with open(pdf_path, 'rb') as pdf_file:
            data = {'file': (pdf_file, 'sample.pdf')}
            response = self.client.post(
                '/api/region_tribs/upload-pdf', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)

        # Print the JSON response
        json_response = response.json
        print(json_response)

        # Additional assertions based on the expected metadata
        # For example:
        self.assertIn('author', json_response)
        self.assertIn('title', json_response)


class TestPDFProcessing(TestCase):
    def create_app(self):
        flask_app.config['TESTING'] = True
        return flask_app

    def test_process_pdf(self):
        # Path to your sample PDF file
        pdf_path = os.path.join(os.path.dirname(
            __file__), 'assets', 'test_region_tribs.pdf')

        # Open the file in binary mode
        with open(pdf_path, 'rb') as pdf_file:
            data = {
                'file': (pdf_file, 'sample.pdf')
            }
            response = self.client.post('/api/region_tribs/process_pdf', data=data, content_type='multipart/form-data')
            assert response.status_code == 200
            # Add additional assertions based on the expected response structure


# ========= Tools


class TestAnnotationsExtractor:
    @pytest.fixture
    def extractor(self):
        # Use a sample PDF path here
        pdf_path = os.path.join(os.path.dirname(
            __file__), 'assets', 'test_region_tribs.pdf')
        return AnnotationsExtractor(pdf_path)

    def test_parse_scale_line_inches(self, extractor):
        scale_line = "1'-6\""
        # Assuming the scale line represents 18 inches
        assert extractor.parse_scale_line_inches(scale_line) == 18

    def test_extract_real_world_coordinates(self, extractor):
        # Test this method with a known page number and expected annotations
        # print("Testing test_extract_real_world_coordinates")
        # print(extractor.extract_real_world_coordinates(0))
        pass

class TestAreaElementAnalyzer:
    def test_process_data(self):
        mock_data = {
            'annotations': [
                # Add mock annotation data here
            ]
        }
        analyzer = AreaElementAnalyzer(mock_data)
        # Assertions to check if areas, floors, roofs, and walls are processed correctly

    def test_calculate_intersection_lengths(self):
        # Similar to test_process_data, but also checks intersection lengths
        pass


class TestAreaAnalysisReport:
    def test_generate_report(self):
        mock_area_analysis = {
            # Populate with mock area analysis data
        }
        mock_example_data = {
            'page_metadata': {
                'weight_criteria': {
                    # Populate with mock weight criteria
                }
            }
        }
        report = AreaAnalysisReport(mock_area_analysis, mock_example_data)
        report_df = report.generate_report()
        # Assertions to check the contents of the report DataFrame


# Run the tests if this file is executed
if __name__ == '__main__':
    pytest.main()
