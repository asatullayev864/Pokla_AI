"""
Birinchi superadmin hisobini yaratish (yoki mavjudining parolini yangilash) uchun skript.

Ishga tushirish (loyiha papkasining ildizidan):
    python create_superadmin.py
"""
import getpass

from database.db import init_db, upsert_superadmin
from auth.security import hash_password


def main():
    print("=== Superadmin yaratish ===\n")

    username = input("Login: ").strip()
    password = getpass.getpass("Parol: ").strip()
    password2 = getpass.getpass("Parolni takrorlang: ").strip()

    if not username or not password:
        print("\n❌  Login va parol bo'sh bo'lmasligi kerak")
        return

    if password != password2:
        print("\n❌  Parollar mos kelmadi")
        return

    if len(password) < 6:
        print("\n❌  Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return

    init_db()  # users jadvali mavjudligiga ishonch hosil qilamiz
    user = upsert_superadmin(username, hash_password(password))

    print(f"\n✅  Superadmin tayyor: {user['username']} (id={user['id']})")
    print("Endi shu login va parol bilan saytga kirishingiz mumkin.")


if __name__ == "__main__":
    main()

