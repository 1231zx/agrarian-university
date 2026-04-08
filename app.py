from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, abort
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_caching import Cache
from config import Config
from models import db, User, Program, News, Contact, PageContent, Page
from sqlalchemy import text
from datetime import datetime, timedelta
import calendar
import os
import pandas as pd
import pdfplumber
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    CORS(app)
    
    mail = Mail(app)
    cache = Cache(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    from api import init_api
    init_api(app)

    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ Подключение к PostgreSQL успешно!")
            db.create_all()
            print("✅ Таблицы созданы/проверены")
            
            # Создаем тестовые институты и кафедры, если их нет
            if Page.query.filter_by(template='institute').count() == 0:
                create_default_pages()
                
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")

    RASP_FOLDER = os.path.join(os.path.dirname(__file__), 'rasp')
    os.makedirs(RASP_FOLDER, exist_ok=True)

    # ==================== КОНФИГУРАЦИЯ РАСПИСАНИЯ ====================
    SCHEDULE_CONFIG = {
        'class schedule 1st year 2nd semester full-time study.pdf': {
            'title': '1 курс (2 семестр)', 'description': 'Расписание занятий для 1 курса, очная форма', 'institute': 'Все институты'
        },
        'class schedule 2nd year 4th semester full-time study.pdf': {
            'title': '2 курс (4 семестр)', 'description': 'Расписание занятий для 2 курса, очная форма', 'institute': 'Все институты'
        },
        'CPSSZ2.xls': {'title': 'ЦПССЗ - все курсы', 'description': 'Расписание для Центра подготовки специалистов среднего звена', 'institute': 'ЦПССЗ'},
        'IAT2.xls': {'title': 'ИАЭТ - все курсы', 'description': 'Институт агроэкологических технологий', 'institute': 'ИАЭТ'},
        'IEU2.xls': {'title': 'ИЭиУ АПК - все курсы', 'description': 'Институт экономики и управления АПК', 'institute': 'ИЭиУ АПК'},
        'IiSiE2.xlsx': {'title': 'ИИСиЭ - расписание', 'description': 'Институт информационных систем и инженерии', 'institute': 'ИИСиЭ'},
        'IPBVM2.xls': {'title': 'ИПБиВМ - все курсы', 'description': 'Институт прикладной биотехнологии', 'institute': 'ИПБиВМ'},
        'IPP2.xls': {'title': 'ИПП - все курсы', 'description': 'Институт пищевых производств', 'institute': 'ИПП'},
        'IZKP2.xls': {'title': 'ИЗКиП - все курсы', 'description': 'Институт землеустройства, кадастров', 'institute': 'ИЗКиП'},
        'UI2.xlsx': {'title': 'Юридический институт', 'description': 'Юридический институт', 'institute': 'ЮИ'},
    }

    # ==================== ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ВСЕХ СТРАНИЦ ====================
    def create_default_pages():
        # Полный список всех страниц
        all_pages = [
            ('university_main', 'Университет', 'university_section', None, '<h2>Красноярский государственный аграрный университет</h2><p>Ведущий аграрный вуз Сибири.</p>'),
            ('student_main', 'Студенту', 'student_section', None, '<h2>Студенческая жизнь</h2>'),
            ('applicant_main', 'Поступающему', 'applicant_section', None, '<h2>Поступающим</h2>'),
            ('science', 'Научная деятельность', 'science_section', None, '<h2>Научная деятельность</h2><p>Красноярский ГАУ ведет активную научную деятельность.</p>'),
            ('laboratories', 'Инновационные лаборатории', 'science_section', None, '<h2>Инновационные лаборатории</h2>'),
            ('science_schools', 'Научные школы', 'science_section', None, '<h2>Научные школы</h2>'),
            ('grants', 'Гранты и конкурсы', 'science_section', None, '<h2>Гранты и конкурсы</h2>'),
            ('conferences', 'Конференции', 'science_section', None, '<h2>Конференции</h2>'),
            ('science_news', 'Новости науки', 'science_section', None, '<h2>Новости науки</h2>'),
            ('school_info', 'Информация для школьников', 'info_page', None, '<h2>Информация для школьников</h2>'),
            ('olympiads', 'Олимпиады и конкурсы', 'info_page', None, '<h2>Олимпиады</h2>'),
            ('preparatory_courses', 'Подготовительные курсы', 'info_page', None, '<h2>Подготовительные курсы</h2>'),
            ('agro_classes', 'Агроклассы', 'info_page', None, '<h2>Агроклассы</h2>'),
            ('career_guidance', 'Профориентационная работа', 'info_page', None, '<h2>Профориентация</h2>'),
            ('school_awards', 'Наши награды', 'info_page', None, '<h2>Наши награды</h2>'),
            ('postgraduate', 'Аспирантура', 'info_page', None, '<h2>Аспирантура</h2>'),
            ('doctoral', 'Докторантура', 'info_page', None, '<h2>Докторантура</h2>'),
            ('attestation', 'Аттестация', 'info_page', None, '<h2>Аттестация</h2>'),
            ('candidate_exams', 'Кандидатские экзамены', 'info_page', None, '<h2>Кандидатские экзамены</h2>'),
            ('dissertations', 'Диссертации', 'info_page', None, '<h2>Диссертации</h2>'),
            ('science_supervisors', 'Научные руководители', 'info_page', None, '<h2>Научные руководители</h2>'),
            ('employee', 'Сотруднику', 'info_page', None, '<h2>Сотруднику</h2>'),
            ('employer', 'Работодателю', 'info_page', None, '<h2>Работодателю</h2>'),
            ('alumni', 'Выпускнику', 'info_page', None, '<h2>Выпускнику</h2>'),
            ('contacts_departments', 'Контакты подразделений', 'info_page', None, '<h2>Контакты подразделений</h2>'),
        ]
        
        for slug, title, template, parent_slug, content in all_pages:
            page = Page.query.filter_by(slug=slug).first()
            if not page:
                # Создаем новую страницу
                page = Page(
                    slug=slug,
                    title=title,
                    content=content,
                    template=template,
                    published=True
                )
                db.session.add(page)
                print(f"✅ Создана страница: {slug}")
            else:
                # Обновляем существующую, если контент пустой
                if not page.content or len(page.content) < 50:
                    page.content = content
                    page.title = title
                    page.template = template
                    page.published = True
                    print(f"🔄 Обновлена страница: {slug}")
        
        # Создаем институты
        institutes = [
            ('institute_agro', 'Институт агроэкологических технологий', '<h2>Институт агроэкологических технологий</h2>'),
            ('institute_economy', 'Институт экономики и управления АПК', '<h2>Институт экономики и управления АПК</h2>'),
            ('institute_engineering', 'Институт инженерных систем и энергетики', '<h2>Институт инженерных систем и энергетики</h2>'),
            ('institute_biotech', 'Институт прикладной биотехнологии', '<h2>Институт прикладной биотехнологии</h2>'),
            ('institute_food', 'Институт пищевых производств', '<h2>Институт пищевых производств</h2>'),
            ('institute_land', 'Институт землеустройства', '<h2>Институт землеустройства</h2>'),
            ('institute_law', 'Юридический институт', '<h2>Юридический институт</h2>'),
            ('institute_achinsk', 'Ачинский филиал', '<h2>Ачинский филиал</h2>'),
        ]
        
        for slug, title, content in institutes:
            if not Page.query.filter_by(slug=slug).first():
                page = Page(slug=slug, title=title, content=content, template='institute', published=True)
                db.session.add(page)
                print(f"✅ Создан институт: {slug}")
        
        db.session.commit()
        print("✅ Все страницы проверены/созданы")

    # ==================== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ====================
    def read_excel_file(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        try:
            excel_file = pd.ExcelFile(filepath)
            html_parts = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                html_parts.append(f'<div class="schedule-sheet"><h3 class="schedule-sheet-title">{sheet_name}</h3><div class="schedule-readable-content">')
                for idx, row in df.iterrows():
                    if row.isna().all():
                        continue
                    cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
                    if len(cells) >= 3:
                        lesson_type = 'practice'
                        if 'лекц' in cells[1].lower():
                            lesson_type = 'lecture'
                        elif 'лаб' in cells[1].lower():
                            lesson_type = 'lab'
                        html_parts.append(f'<div class="schedule-lesson-card" data-type="{lesson_type}"><div class="schedule-lesson-time">{cells[0]}</div><div class="schedule-lesson-details"><span class="schedule-lesson-subject">{cells[1]}</span><span class="schedule-lesson-teacher">{cells[2]}</span>{f"<span class=\"schedule-lesson-room\">{cells[3]}</span>" if len(cells) > 3 else ""}</div></div>')
                    elif len(cells) == 2:
                        html_parts.append(f'<div class="schedule-info-row"><strong>{cells[0]}:</strong> {cells[1]}</div>')
                    else:
                        html_parts.append(f"<p class='schedule-text-line'>{cells[0]}</p>")
                html_parts.append("</div></div>")
            return "".join(html_parts)
        except Exception as e:
            return f"<div class='schedule-error'>Ошибка чтения Excel: {str(e)}</div>"

    def format_file_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} Б"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} КБ"
        else:
            return f"{size_bytes/(1024*1024):.1f} МБ"

    def get_file_icon(ext):
        icons = {'.pdf': '📄', '.xls': '📊', '.xlsx': '📊'}
        return icons.get(ext.lower(), '📁')

    # ==================== МАРШРУТЫ АДМИН ПАНЕЛИ ====================
    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return render_template('admin.html')

    @app.route('/admin/pages')
    @login_required
    def admin_pages():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        all_pages = Page.query.order_by(Page.template, Page.title).all()
        return render_template('admin_pages.html', all_pages=all_pages)

    @app.route('/admin/page/create', methods=['GET', 'POST'])
    @login_required
    def admin_page_create():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        if request.method == 'POST':
            page = Page(
                slug=request.form['slug'],
                title=request.form['title'],
                content=request.form['content'],
                template=request.form['template'],
                parent_id=request.form.get('parent_id') or None,
                meta_description=request.form.get('meta_description'),
                published='published' in request.form
            )
            db.session.add(page)
            db.session.commit()
            flash(f'Страница "{page.title}" создана!', 'success')
            return redirect(url_for('admin_pages'))
        parents = Page.query.filter_by(template='institute').all()
        return render_template('admin_page_form.html', parents=parents)

    @app.route('/admin/page/<int:page_id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_page_edit(page_id):
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        page = Page.query.get_or_404(page_id)
        if request.method == 'POST':
            page.title = request.form['title']
            page.content = request.form['content']
            page.meta_description = request.form.get('meta_description')
            page.published = 'published' in request.form
            db.session.commit()
            flash(f'Страница "{page.title}" сохранена!', 'success')
            return redirect(url_for('admin_pages'))
        return render_template('admin_page_edit.html', page=page)

    @app.route('/admin/page/<int:page_id>/delete', methods=['POST'])
    @login_required
    def admin_page_delete(page_id):
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Нет доступа'})
        page = Page.query.get_or_404(page_id)
        db.session.delete(page)
        db.session.commit()
        return jsonify({'success': True})

    # ==================== ДИНАМИЧЕСКИЕ СТРАНИЦЫ ====================
    @app.route('/page/<slug>')
    def dynamic_page(slug):
        page = Page.query.filter_by(slug=slug, published=True).first_or_404()
        children = Page.query.filter_by(parent_id=page.id, published=True).order_by(Page.menu_order).all()
        
        # Список шаблонов, которые лежат в папке dynamic/
        dynamic_templates = ['applicant_section', 'department', 'info_page', 'institute', 'science_section', 'student_section', 'university_section']
        
        if page.template in dynamic_templates:
            return render_template(f'dynamic/{page.template}.html', page=page, children=children)
        else:
            return render_template(f'{page.template}.html', page=page, children=children)

    # ==================== СТРАНИЦА ИНСТИТУТОВ ====================
    @app.route('/institutes')
    def institutes_page():
        # Получаем уникальные институты (без дублирования)
        institutes = Page.query.filter_by(template='institute', published=True).distinct(Page.slug).all()
        
        # Для каждого института загружаем кафедры
        for institute in institutes:
            institute.children = Page.query.filter_by(parent_id=institute.id, template='department', published=True).all()
        
        return render_template('dynamic/institutes_page.html', institutes=institutes)

    # ==================== МАРШРУТЫ РАСПИСАНИЯ ====================
    @app.route('/rasp/<path:filename>')
    def serve_rasp_file(filename):
        return send_from_directory(RASP_FOLDER, filename, as_attachment=True)

    @app.route('/schedule')
    def schedule_list():
        files = []
        for f in os.listdir(RASP_FOLDER):
            filepath = os.path.join(RASP_FOLDER, f)
            if os.path.isfile(filepath):
                ext = os.path.splitext(f)[1].lower()
                config = SCHEDULE_CONFIG.get(f, {'title': f, 'description': 'Расписание занятий', 'institute': 'Другое'})
                files.append({
                    'filename': f, 'title': config['title'], 'description': config['description'],
                    'institute': config['institute'], 'size': format_file_size(os.path.getsize(filepath)),
                    'ext': ext, 'icon': get_file_icon(ext),
                })
        files.sort(key=lambda x: (x['institute'], x['title']))
        grouped_files = {}
        for file in files:
            inst = file['institute']
            if inst not in grouped_files:
                grouped_files[inst] = []
            grouped_files[inst].append(file)
        return render_template('schedule_list.html', grouped_files=grouped_files, institutes=sorted(grouped_files.keys()))

    @app.route('/schedule/view/<path:filename>')
    def schedule_view(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        if not os.path.exists(filepath):
            flash(f'Файл {filename} не найден', 'danger')
            return redirect(url_for('schedule_list'))
        ext = os.path.splitext(filename)[1].lower()
        file_size = format_file_size(os.path.getsize(filepath))
        config = SCHEDULE_CONFIG.get(filename, {'title': filename, 'description': 'Расписание занятий', 'institute': 'Другое'})
        if ext in ['.xls', '.xlsx']:
            content = read_excel_file(filename)
            return render_template('schedule_excel.html', filename=filename, file_title=config['title'],
                                 file_description=config['description'], file_institute=config['institute'],
                                 content=content, file_size=file_size)
        elif ext == '.pdf':
            return render_template('schedule_pdf.html', filename=filename, file_title=config['title'],
                                 file_description=config['description'], file_institute=config['institute'],
                                 file_size=file_size)
        else:
            flash('Неподдерживаемый формат файла', 'warning')
            return redirect(url_for('schedule_list'))

    # ==================== ДИНАМИЧЕСКИЙ ПОИСК ====================
    @app.route('/api/search')
    def api_search():
        query = request.args.get('q', '').strip().lower()
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        results = []
        seen_urls = set()
        
        pages = Page.query.filter(
            db.or_(
                Page.title.ilike(f'%{query}%'),
                Page.content.ilike(f'%{query}%'),
                Page.meta_description.ilike(f'%{query}%')
            ),
            Page.published == True
        ).limit(20).all()
        
        for page in pages:
            url = url_for('dynamic_page', slug=page.slug)
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    'type': page.template,
                    'type_ru': 'Страница',
                    'title': page.title,
                    'url': url,
                    'description': page.meta_description or '',
                    'icon': '📄'
                })
        
        programs = Program.query.filter(
            db.or_(
                Program.name.ilike(f'%{query}%'),
                Program.description.ilike(f'%{query}%')
            )
        ).limit(5).all()
        
        for p in programs:
            url = url_for('program_detail', program_id=p.id)
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    'type': 'program',
                    'type_ru': 'Программа',
                    'title': p.name,
                    'url': url,
                    'description': f'{p.degree} • {p.duration}',
                    'icon': '📚'
                })
        
        return jsonify({'results': results})

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return render_template('search.html', query=query, all_results=[], total_results=0)
        
        results = []
        seen_urls = set()
        
        pages = Page.query.filter(
            db.or_(
                Page.title.ilike(f'%{query}%'),
                Page.content.ilike(f'%{query}%')
            ),
            Page.published == True
        ).limit(50).all()
        
        for page in pages:
            url = url_for('dynamic_page', slug=page.slug)
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    'type': page.template,
                    'type_ru': 'Страница',
                    'title': page.title,
                    'url': url,
                    'description': page.meta_description or '',
                })
        
        return render_template('search.html', query=query, all_results=results, total_results=len(results))

    # ==================== СТАТИЧЕСКИЕ СТРАНИЦЫ ====================
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contacts')
    def contacts():
        return render_template('contacts.html')

    @app.route('/news')
    def news():
        return render_template('news.html')

    @app.route('/programs')
    def programs():
        return render_template('programs.html')

    @app.route('/program/<int:program_id>')
    def program_detail(program_id):
        program = Program.query.get_or_404(program_id)
        program.views += 1
        db.session.commit()
        return render_template('program_detail.html', program=program)

    # ==================== АУТЕНТИФИКАЦИЯ ====================
    @app.route('/send-message', methods=['POST'])
    def send_message():
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        try:
            contact = Contact(name=name, email=email, phone=phone, message=message)
            db.session.add(contact)
            db.session.commit()
            flash('Сообщение отправлено!', 'success')
        except Exception as e:
            print(f"Ошибка: {e}")
            flash('Сообщение сохранено', 'warning')
        return redirect(url_for('contacts'))

    @app.route('/admin/stats')
    @login_required
    def admin_stats():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        total_users = User.query.count()
        total_news = News.query.count()
        total_programs = Program.query.count()
        total_messages = Contact.query.count()
        popular_programs = Program.query.order_by(Program.views.desc()).limit(5).all()
        monthly_stats = []
        months = []
        counts = []
        for i in range(5, -1, -1):
            date = datetime.now() - timedelta(days=30*i)
            month_start = datetime(date.year, date.month, 1)
            if date.month == 12:
                month_end = datetime(date.year+1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(date.year, date.month+1, 1) - timedelta(days=1)
            users_count = User.query.filter(User.created_at >= month_start, User.created_at <= month_end).count()
            messages_count = Contact.query.filter(Contact.created_at >= month_start, Contact.created_at <= month_end).count()
            month_name = calendar.month_name[date.month][:3] + f" {date.year}"
            monthly_stats.append({'month': month_name, 'users': users_count, 'messages': messages_count})
            months.append(month_name)
            counts.append(users_count)
        return render_template('admin_stats.html', total_users=total_users, total_news=total_news,
                             total_programs=total_programs, total_messages=total_messages,
                             popular_programs=popular_programs, monthly_stats=monthly_stats,
                             chart_months=months, chart_counts=counts)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Вы успешно вошли в систему!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if not username or not email or not password:
                flash('Пожалуйста, заполните все поля', 'danger')
                return render_template('register.html')
            if password != confirm_password:
                flash('Пароли не совпадают', 'danger')
                return render_template('register.html')
            if len(password) < 6:
                flash('Пароль должен быть не менее 6 символов', 'danger')
                return render_template('register.html')
            if User.query.filter_by(username=username).first():
                flash('Пользователь с таким именем уже существует', 'danger')
                return render_template('register.html')
            if User.query.filter_by(email=email).first():
                flash('Пользователь с таким email уже существует', 'danger')
                return render_template('register.html')
            user = User(username=username, email=email, is_admin=False)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы', 'success')
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)

    @app.route('/new/<slug>')
    def redirect_old_new(slug):
        return redirect(url_for('dynamic_page', slug=slug), code=301)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)