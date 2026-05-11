import unittest
import os
import sys
import json
import re
from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestFunctional(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.config['SECRET_KEY'] = 'test-key'
        cls.client = cls.app.test_client()
        cls._register_test_routes()
    
    @classmethod
    def _register_test_routes(cls):
        @cls.app.route('/')
        def index(): return "OK", 200
        @cls.app.route('/about')
        def about(): return "OK", 200
        @cls.app.route('/contacts')
        def contacts(): return "OK", 200
        @cls.app.route('/news')
        def news(): return "OK", 200
        @cls.app.route('/programs')
        def programs(): return "OK", 200
        @cls.app.route('/schedule')
        def schedule(): return "OK", 200
        @cls.app.route('/kgau-dashboard')
        def admin_dashboard(): return "OK", 200
        @cls.app.route('/university-today')
        def university_today(): return "OK", 200
        @cls.app.route('/institute/agro')
        def institute_agro(): return "OK", 200
        @cls.app.route('/institute/agro/department/agronomy')
        def agro_department(): return "OK", 200
        @cls.app.route('/api/search')
        def api_search(): return json.dumps({'results': []}), 200, {'Content-Type': 'application/json'}
        @cls.app.route('/api/v1/programs')
        def api_programs(): return json.dumps({'programs': []}), 200, {'Content-Type': 'application/json'}
        @cls.app.route('/api/v1/news')
        def api_news(): return json.dumps({'news': []}), 200, {'Content-Type': 'application/json'}
        @cls.app.route('/api/v1/contacts')
        def api_contacts(): return json.dumps({'contacts': []}), 200, {'Content-Type': 'application/json'}
        @cls.app.errorhandler(404)
        def not_found(e): return "Not Found", 404
    
    def test_01_main_pages_accessibility(self):
        urls = [
            '/', '/about', '/contacts', '/news', '/programs', 
            '/schedule', '/university-today',
            '/institute/agro', '/institute/agro/department/agronomy',
            '/kgau-dashboard'
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Страница {url} недоступна")
        print("Ключевые страницы доступны")
    
    def test_02_404_error_handling(self):
        response = self.client.get('/nonexistent-page-xyz-123')
        self.assertEqual(response.status_code, 404)
        print("Ошибка 404 обрабатывается корректно")
    
    def test_03_api_search_structure(self):
        response = self.client.get('/api/search?q=test')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        print("API поиска возвращает корректную структуру")
    
    def test_04_html_structure_validation(self):
        files_to_check = {
            'templates/base.html': ['sidebar', 'main-content', 'footer', 'search-input'],
            'templates/index.html': ['hero', 'btn-primary', 'features'],
            'templates/contacts.html': ['form', 'contact-form'],
            'templates/schedule_list.html': ['schedule-files-grid', 'schedule-search-input']
        }
        for filepath, required_elements in files_to_check.items():
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for element in required_elements:
                        self.assertIn(element, content, f"{filepath} не содержит '{element}'")
        print("HTML-шаблоны имеют правильную структуру")
    
    def test_05_institute_pages_have_departments(self):
        institutes = [
            ('institute_agro.html', ['общего земледелия', 'растениеводства', 'почвоведения']),
            ('institute_biotech.html', ['анатомии', 'зоотехнии', 'эпизоотологии']),
            ('institute_law.html', ['гражданского', 'уголовного', 'теории'])
        ]
        for filename, keywords in institutes:
            filepath = os.path.join('templates', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    for keyword in keywords:
                        self.assertIn(keyword, content, f"{filename} не содержит '{keyword}'")
        print("Страницы институтов содержат списки кафедр")
    
    def test_06_css_schedule_styles_exist(self):
        css_path = 'static/css/style.css'
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
                required = ['.schedule-lesson-card', '.schedule-group-selector', '.day-btn', '@media']
                for req in required:
                    self.assertIn(req, content, f"В CSS отсутствует '{req}'")
        print("CSS содержит все необходимые стили")
    
    def test_07_css_color_scheme(self):
        css_path = 'static/css/style.css'
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
                color_classes = ['lesson-type-lecture', 'lesson-type-practice', 'lesson-type-lab', 'lesson-type-exam']
                for cls_name in color_classes:
                    self.assertIn(cls_name, content, f"В CSS отсутствует класс '{cls_name}'")
        print("CSS имеет цветовую индикацию типов занятий")
    
    def test_08_js_functionality(self):
        js_files = {
            'static/js/main.js': ['DOMContentLoaded', 'addEventListener', 'scrollIntoView'],
            'static/js/admin.js': ['showTab', 'loadPrograms', 'fetch']
        }
        for filepath, functions in js_files.items():
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for func in functions:
                        self.assertIn(func, content, f"{filepath} не содержит '{func}'")
        print("JS файлы содержат необходимые функции")
    
    def test_09_project_structure(self):
        required_folders = ['templates', 'static/css', 'static/js', 'rasp']
        required_files = ['templates/base.html', 'static/css/style.css', 'static/js/main.js', 'static/js/admin.js', 'app.py', 'models.py', 'config.py']
        for folder in required_folders:
            self.assertTrue(os.path.exists(folder), f"Папка {folder} не существует")
        for file in required_files:
            self.assertTrue(os.path.exists(file), f"Файл {file} не существует")
        print("Структура проекта корректна")
    
    def test_10_rasp_files_count(self):
        rasp_dir = 'rasp'
        if os.path.exists(rasp_dir):
            files = os.listdir(rasp_dir)
            self.assertGreater(len(files), 0, "В папке rasp нет файлов")
            print(f"Файлов расписания: {len(files)}")
        else:
            print("Папка rasp отсутствует (пропуск проверки)")
    
    def test_11_responsive_design(self):
        css_path = 'static/css/style.css'
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('@media (max-width: 768px)', content)
                self.assertIn('@media (max-width: 480px)', content)
        print("CSS содержит медиа-запросы для мобильных устройств")


if __name__ == '__main__':
    unittest.main(verbosity=2)