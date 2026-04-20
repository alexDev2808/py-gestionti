from app.config.database import test_connection

ok, message = test_connection()
print(ok, message)