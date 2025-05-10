from django.test import TestCase, Client
from chat.services.confidence_service import confidence_interval

class ConfidenceServiceTest(TestCase):
    def test_averages_two_values(self):
        data = [5,10]
        mean, cinf, csup = confidence_interval(data, 0.95)
        self.assertEqual(mean, 7.5)
        