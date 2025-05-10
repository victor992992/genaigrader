from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from chat.models import Course
from unittest.mock import patch, MagicMock
from io import BytesIO

class ExamViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        # Crea datos de prueba
        self.course = Course.objects.create(name="Matemáticas", user=self.user)

    def test_exam_view_requires_login(self):
        response = self.client.get(reverse("exam"))  
        self.assertEqual(response.status_code, 302)  

    def test_exam_view_returns_200_for_logged_in_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse("exam"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "exam.html")
        self.assertContains(response, "Matemáticas")

    def test_exam_view_doesnt_contain_nonexistent_subject(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse("exam"))
        self.assertNotContains(response, "Sistemas Operativos")


class UploadFileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_login(self.user)

    @patch("chat.services.course_service.get_or_create_course")
    @patch("chat.services.exam_service.create_exam")
    @patch("chat.services.model_service.get_or_create_model")
    @patch("chat.services.file_service.save_uploaded_file")
    @patch("chat.services.exam_service.process_exam_file")
    @patch("chat.llm_api.LlmApi")
    @patch("chat.services.stream_service.stream_responses")
    def test_upload_file_success(
        self, mock_stream, mock_llm_class, mock_process, mock_save_file,
        mock_get_model, mock_create_exam, mock_get_course
    ):
        mock_get_course.return_value = MagicMock()
        mock_create_exam.return_value = MagicMock()
        mock_get_model.return_value = MagicMock()
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.validate.return_value = True
        mock_save_file.return_value = "/fake/path"
        mock_process.return_value = ["Pregunta 1", "Pregunta 2"]
        mock_stream.return_value = iter(["data: respuesta 1\n", "data: respuesta 2\n"])

        file_data = BytesIO(b"Contenido del archivo")
        file_data.name = "examen.pdf"

        response = self.client.post(
            reverse("upload_file"),  
            {
                "file": file_data,
                "user_prompt": "Explica cada pregunta"
            }
        )
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/event-stream")

from chat.services.confidence_service import confidence_interval

class ConfidenceServiceTest(TestCase):
    def test_averages_two_values(self):
        data = [5,10]
        mean, cinf, csup = confidence_interval(data, 0.95)
        self.assertEqual(mean, 7.5)
        