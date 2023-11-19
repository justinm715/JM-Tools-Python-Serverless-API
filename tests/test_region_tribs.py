import pytest
from api.region_tribs import app as flask_app
from flask_testing import TestCase
from werkzeug.datastructures import FileStorage
import os


class TestApp(TestCase):
    def create_app(self):
        flask_app.config['TESTING'] = True
        return flask_app

    def test_time(self):
        response = self.client.get('/time')
        assert response.status_code == 200
        assert "time" in response.json

    def test_random_number(self):
        response = self.client.get('/api/region_tribs/random_number')
        assert response.status_code == 200
        assert "random_number" in response.json
        assert 1 <= response.json["random_number"] <= 100


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
                '/upload-pdf', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)

        # Print the JSON response
        json_response = response.json
        print(json_response)

        # Additional assertions based on the expected metadata
        # For example:
        self.assertIn('author', json_response)
        self.assertIn('title', json_response)


# Run the tests if this file is executed
if __name__ == '__main__':
    pytest.main()
