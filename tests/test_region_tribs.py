import pytest
from api.index import app as flask_app
from flask_testing import TestCase


class TestApp(TestCase):
    def create_app(self):
        flask_app.config['TESTING'] = True
        return flask_app

    def test_time(self):
        response = self.client.get('/time')
        assert response.status_code == 200
        assert "time" in response.json

    def test_random_number(self):
        response = self.client.get('/random')
        assert response.status_code == 200
        assert "random_number" in response.json
        assert 1 <= response.json["random_number"] <= 100


# Run the tests if this file is executed
if __name__ == '__main__':
    pytest.main()
