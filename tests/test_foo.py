import pytest
from tools.foo import RandomNumberGenerator
from flask_testing import TestCase
from api.region_tribs import app


def test_random_number_generator():
    rng = RandomNumberGenerator(1, 10)
    number = rng.generate()
    assert 1 <= number <= 10

    rng = RandomNumberGenerator(100, 200)
    number = rng.generate()
    assert 100 <= number <= 200


class TestAPI(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_random_number_route(self):
        response = self.client.get('/api/region_tribs/random_number')
        assert response.status_code == 200
        data = response.json
        assert 'random_number' in data
        assert 1 <= data['random_number'] <= 100  # Assuming default bounds


if __name__ == '__main__':
    pytest.main()
