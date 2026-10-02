import time, unittest
from types import SimpleNamespace
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

class SecurityTests(unittest.TestCase):
    def test_password_round_trip(self):
        encoded=hash_password("SecurePass123!")
        self.assertTrue(verify_password("SecurePass123!",encoded))
        self.assertFalse(verify_password("wrong-password",encoded))
        self.assertNotIn("SecurePass123!",encoded)
    def test_signed_token_contains_identity(self):
        token=create_access_token(SimpleNamespace(id=7,email="agent@example.com",role="agent"))
        claims=decode_access_token(token)
        self.assertEqual(claims["sub"],"7")
        self.assertEqual(claims["role"],"agent")
        self.assertGreater(claims["exp"],int(time.time()))

if __name__=="__main__": unittest.main()
