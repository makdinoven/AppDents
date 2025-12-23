import os
import sys
import unittest
from unittest.mock import patch


# Ensure `/workspace/backend` is on sys.path so `app.*` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Minimal env required to import app settings during tests.
# (The app Settings object is instantiated at import-time.)
_REQUIRED_ENV: dict[str, str] = {
    "APP_URL": "http://localhost",
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_HOST": "localhost",
    "DB_PORT": "3306",
    "DB_NAME": "test",
    "SECRET_KEY": "test-secret",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "STRIPE_SECRET_KEY_RU": "x",
    "STRIPE_PUBLISHABLE_KEY_RU": "x",
    "STRIPE_WEBHOOK_SECRET_RU": "x",
    "STRIPE_SECRET_KEY_EN": "x",
    "STRIPE_PUBLISHABLE_KEY_EN": "x",
    "STRIPE_WEBHOOK_SECRET_EN": "x",
    "STRIPE_SECRET_KEY_ES": "x",
    "STRIPE_PUBLISHABLE_KEY_ES": "x",
    "STRIPE_WEBHOOK_SECRET_ES": "x",
    "STRIPE_PMC_RU": "x",
    "STRIPE_PMC_ES": "x",
    "STRIPE_PMC_EN": "x",
    "EMAIL_SENDER": "noreply@example.com",
    "FACEBOOK_PIXEL_ID": "x",
    "FACEBOOK_ACCESS_TOKEN": "x",
    "FACEBOOK_PIXEL_ID_LEARNWORLDS": "x",
    "FACEBOOK_ACCESS_TOKEN_LEARNWORLDS": "x",
    "FACEBOOK_PIXEL_ID_DONATION": "x",
    "FACEBOOK_ACCESS_TOKEN_DONATION": "x",
    "FACEBOOK_PIXEL_ID_RU": "x",
    "FACEBOOK_ACCESS_TOKEN_RU": "x",
    "FACEBOOK_PIXEL_ID_EN": "x",
    "FACEBOOK_ACCESS_TOKEN_EN": "x",
    "FACEBOOK_PIXEL_ID_ES": "x",
    "FACEBOOK_ACCESS_TOKEN_ES": "x",
    "FACEBOOK_PIXEL_ID_IT": "x",
    "FACEBOOK_ACCESS_TOKEN_IT": "x",
    "FACEBOOK_PIXEL_ID_1_DOLLAR": "x",
    "FACEBOOK_ACCESS_TOKEN_1_DOLLAR": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_4": "x",
    "FACEBOOK_PIXEL_ID_NEW_4": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_5": "x",
    "FACEBOOK_PIXEL_ID_NEW_5": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_11": "x",
    "FACEBOOK_PIXEL_ID_NEW_11": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_10": "x",
    "FACEBOOK_PIXEL_ID_NEW_10": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_12": "x",
    "FACEBOOK_PIXEL_ID_NEW_12": "x",
    "FACEBOOK_ACCESS_TOKEN_NEW_13": "x",
    "FACEBOOK_PIXEL_ID_NEW_13": "x",
    "PLACID_API_KEY": "x",
}
for k, v in _REQUIRED_ENV.items():
    os.environ.setdefault(k, v)


from app.services_v2 import landing_service  # noqa: E402


class RecommendTagsPropagationTest(unittest.TestCase):
    def test_recommend_branch_passes_tags_to_recommended_service(self) -> None:
        db = object()  # not used in recommend branch (mocked)

        with patch.object(landing_service, "get_recommended_landing_cards") as mocked:
            mocked.return_value = {"total": 0, "cards": []}

            landing_service.get_personalized_landing_cards(
                db,
                user_id=123,
                skip=0,
                limit=20,
                tags=["ortho", "surgery"],
                sort="recommend",
                language="EN",
            )

            mocked.assert_called_once()
            _, kwargs = mocked.call_args
            self.assertEqual(kwargs["tags"], ["ortho", "surgery"])

