import os

class Config:
    # Читаем из переменных окружения или .env файла
    def _get_env(key, default=None):
        """Читает переменную из окружения"""
        return os.environ.get(key, default)
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'agrarian-university-secret-key-2025')
    
    # База данных
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '123')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'ARGAGKA')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Почта
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.mail.ru')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'ivanichtur@list.ru')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'SPLFTtXosEsBh1xRaQiK')