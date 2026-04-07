from app import create_app
from models import db, User
from werkzeug.security import check_password_hash

app = create_app()
with app.app_context():
    username = input("Введите логин: ")
    password = input("Введите пароль: ")
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        print(f"✅ Пользователь найден: {user.username}")
        print(f"   is_admin: {user.is_admin}")
        print(f"   Хеш пароля: {user.password_hash[:50]}...")
        
        # Проверяем пароль
        is_correct = check_password_hash(user.password_hash, password)
        print(f"   Пароль верный: {is_correct}")
    else:
        print(f"❌ Пользователь {username} не найден")