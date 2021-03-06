import datetime
import Factory

from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.core.urlresolvers import reverse

from .models import Question
from django.contrib.auth.models import User, AnonymousUser
from .views import IndexView


class QuestionFactory(Factory.Factory):
    def post_make(self):
        pass


class SimpleTest(TestCase):
    def setUp(self):
        # Every test needs access to the request factory
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
                username='jacob', email='jacob@thebeatles.com', password='top_secret')

    def test_detail(self):
        # Create an instance of a GET request.
        request = self.factory.get(reverse('polls:index'))

        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        request.user = self.user
        # Or you can simulate an anonymous user by setting request.user to
        # an AnonymousUser instance.
        request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /polls/
        response = IndexView.as_view()(request)
        self.assertEqual(response.status_code, 200)


class QuestionMethodTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently () should return False for questions whose
        pub_date is in the future
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertEqual(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is older than 1 day.
        :return: None
        """

        time = timezone.now() - datetime.timedelta(days=30)
        old_question = Question(pub_date=time)
        self.assertEqual(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() should return True for questions whose
        pub_date is within the last day.
        :return: None
        """
        time = timezone.now() - datetime.timedelta(hours=1)
        recent_question = Question(pub_date=time)
        self.assertEqual(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Creates a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    :param question_text:
    :param days:
    :return: Question
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionViewTest(TestCase):
    def test_index_view_with_no_question(self):
        """
        If no questions exist, an appropriate message should be displayed.
        :return: None
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_a_future_question(self):
        """
        Question with pub_date in the future should not be displayed on
        the index page.
        :return: None
        """
        create_question(question_text="Future question", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_a_past_question(self):
        """
        Questions with a pub_date in the past should be displayed on the
        index page.
        :return: None
        """
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], ['<Question: Past question.>'])

    def test_index_view_with_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        should be displayed.
        """
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
                response.context['latest_question_list'], ['<Question: Past question.>']
        )

    def test_index_view_with_two_past_questions(self):
        create_question(question_text="Past question2.", days=-30)
        create_question(question_text="Past question1.", days=-5)
        response = self.client.get(reverse('polls:index'))

        self.assertQuerysetEqual(response.context['latest_question_list'], ['<Question: Past question1.>',
                                                                            '<Question: Past question2.>'])
