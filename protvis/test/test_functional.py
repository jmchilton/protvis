from unittest import TestCase
from webtest import TestApp


class FunctionalTestCase(TestCase):

    def setUp(self):
        from protvis import main
        app = main({})
        self.test_app = TestApp(app)


class MainFunctinalTestCase(FunctionalTestCase):

    def test_root(self):
        res = self.test_app.get('/', status=200)
        assert res.body
