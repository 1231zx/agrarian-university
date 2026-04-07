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

# Импортируем все статические страницы из сгенерированного файла
from pages_data import PAGES

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
            # Создаём таблицы только для пользователей, программ, новостей, контактов
            db.create_all()
            print("✅ Таблицы созданы/проверены")
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")

    RASP_FOLDER = os.path.join(os.path.dirname(__file__), 'rasp')
    os.makedirs(RASP_FOLDER, exist_ok=True)

    # ==================== КОНФИГУРАЦИЯ РАСПИСАНИЯ ====================
    SCHEDULE_CONFIG = {
        'class schedule 1st year 2nd semester full-time study.pdf': {
            'title': '1 курс (2 семестр)',
            'description': 'Расписание занятий для 1 курса, очная форма',
            'institute': 'Все институты'
        },
        'class schedule 2nd year 4th semester full-time study.pdf': {
            'title': '2 курс (4 семестр)',
            'description': 'Расписание занятий для 2 курса, очная форма',
            'institute': 'Все институты'
        },
        'Introductory instructions.pdf': {
            'title': 'Вступительные испытания - инструкция',
            'description': 'Инструкция для поступающих, правила проведения экзаменов',
            'institute': 'Абитуриентам'
        },
        'Schedule of consultations for undergraduate programs and exams.pdf': {
            'title': 'Консультации для бакалавров',
            'description': 'Расписание консультаций по программам бакалавриата',
            'institute': 'Бакалавриат'
        },
        'Schedule of consultations on Master\'s degree programs.pdf': {
            'title': 'Консультации для магистров',
            'description': 'Расписание консультаций по программам магистратуры',
            'institute': 'Магистратура'
        },
        'Schedule of entrance examinations for Master\'s degree programs.pdf': {
            'title': 'Вступительные экзамены - магистратура',
            'description': 'Расписание вступительных испытаний в магистратуру',
            'institute': 'Абитуриентам'
        },
        'Schedule of entrance exams for bachelor\'s and specialist programs.pdf.pdf': {
            'title': 'Вступительные экзамены - бакалавриат и специалитет',
            'description': 'Расписание вступительных испытаний',
            'institute': 'Абитуриентам'
        },
        'CPSSZ2.xls': {'title': 'ЦПССЗ - все курсы', 'description': 'Расписание для Центра подготовки специалистов среднего звена (1-4 курсы)', 'institute': 'ЦПССЗ'},
        'IAT2.xls': {'title': 'ИАЭТ - все курсы', 'description': 'Институт агроэкологических технологий (1-4 курсы)', 'institute': 'ИАЭТ'},
        'IEU2.xls': {'title': 'ИЭиУ АПК - все курсы', 'description': 'Институт экономики и управления АПК (1-4 курсы)', 'institute': 'ИЭиУ АПК'},
        'IEUv2.xls': {'title': 'ИЭиУ АПК - вечернее отделение', 'description': 'Институт экономики и управления АПК, вечерняя форма', 'institute': 'ИЭиУ АПК'},
        'IiSiE2.xlsx': {'title': 'ИИСиЭ - расписание', 'description': 'Институт информационных систем и инженерии', 'institute': 'ИИСиЭ'},
        'IPBVM2.xls': {'title': 'ИПБиВМ - все курсы', 'description': 'Институт прикладной биотехнологии и ветеринарной медицины', 'institute': 'ИПБиВМ'},
        'IPP2.xls': {'title': 'ИПП - все курсы', 'description': 'Институт пищевых производств', 'institute': 'ИПП'},
        'IZKP2.xls': {'title': 'ИЗКиП - все курсы', 'description': 'Институт землеустройства, кадастров и природообустройства', 'institute': 'ИЗКиП'},
        'UI2.xlsx': {'title': 'Юридический институт - расписание', 'description': 'Юридический институт', 'institute': 'ЮИ'},
        'UIv2.xlsx': {'title': 'Юридический институт - вечернее отделение', 'description': 'Юридический институт, вечерняя форма', 'institute': 'ЮИ'}
    }

    # ==================== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ====================
    def read_excel_file(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        try:
            excel_file = pd.ExcelFile(filepath)
            html_parts = []
            groups = {}
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                group_name = sheet_name
                if 'групп' in sheet_name.lower() or 'курс' in sheet_name.lower():
                    group_name = sheet_name
                else:
                    for idx in range(min(5, len(df))):
                        row_text = ' '.join([str(cell) for cell in df.iloc[idx] if pd.notna(cell)])
                        if 'группа' in row_text.lower() or 'групп' in row_text.lower():
                            group_name = row_text[:50].strip()
                            break
                lessons = []
                for idx, row in df.iterrows():
                    if row.isna().all():
                        continue
                    cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
                    if len(cells) >= 3:
                        lesson_type = 'practice'
                        subject_lower = cells[1].lower() if len(cells) > 1 else ''
                        if 'лекц' in subject_lower:
                            lesson_type = 'lecture'
                        elif 'лаб' in subject_lower:
                            lesson_type = 'lab'
                        elif 'экзам' in subject_lower:
                            lesson_type = 'exam'
                        day_of_week = 'unknown'
                        time_lower = cells[0].lower()
                        if 'пн' in time_lower:
                            day_of_week = 'mon'
                        elif 'вт' in time_lower:
                            day_of_week = 'tue'
                        elif 'ср' in time_lower:
                            day_of_week = 'wed'
                        elif 'чт' in time_lower:
                            day_of_week = 'thu'
                        elif 'пт' in time_lower:
                            day_of_week = 'fri'
                        elif 'сб' in time_lower:
                            day_of_week = 'sat'
                        lessons.append({
                            'time': cells[0], 'subject': cells[1], 'teacher': cells[2] if len(cells) > 2 else '',
                            'room': cells[3] if len(cells) > 3 else '', 'type': lesson_type, 'day': day_of_week
                        })
                if lessons:
                    if group_name not in groups:
                        groups[group_name] = []
                    groups[group_name].extend(lessons)
            if groups:
                unique_id = filename.replace('.', '_').replace(' ', '_').replace('-', '_')
                html_parts.append(f'<div class="schedule-group-selector" data-unique="{unique_id}"><label>Выберите группу:</label><select id="schedule-group-select-{unique_id}" class="schedule-group-select">')
                for i, group_name in enumerate(groups.keys()):
                    selected = 'selected' if i == 0 else ''
                    html_parts.append(f'<option value="{i}" {selected}>{group_name}</option>')
                html_parts.append('</select></div>')
                for i, (group_name, lessons) in enumerate(groups.items()):
                    display_style = "block" if i == 0 else "none"
                    lessons_by_day = {'mon': [], 'tue': [], 'wed': [], 'thu': [], 'fri': [], 'sat': [], 'unknown': []}
                    for lesson in lessons:
                        day = lesson['day']
                        if day in lessons_by_day:
                            lessons_by_day[day].append(lesson)
                        else:
                            lessons_by_day['unknown'].append(lesson)
                    html_parts.append(f'<div id="group-{unique_id}-{i}" class="schedule-group-container" style="display: {display_style};">')
                    html_parts.append(f'<h3 class="schedule-group-title">{group_name}</h3>')
                    html_parts.append('<div class="schedule-day-switcher-inner">')
                    for day_key, day_name in [('all','Все дни'),('mon','ПН'),('tue','ВТ'),('wed','СР'),('thu','ЧТ'),('fri','ПТ'),('sat','СБ')]:
                        active = 'active' if day_key == 'all' else ''
                        html_parts.append(f'<button class="day-btn-inner {active}" data-day="{day_key}">{day_name}</button>')
                    html_parts.append('</div>')
                    day_names = {'mon':'Понедельник','tue':'Вторник','wed':'Среда','thu':'Четверг','fri':'Пятница','sat':'Суббота','unknown':'Другое'}
                    for day_key, day_name in day_names.items():
                        if lessons_by_day.get(day_key) and len(lessons_by_day[day_key]) > 0:
                            html_parts.append(f'<div class="schedule-day-section" data-day="{day_key}"><h4 class="schedule-day-title">{day_name}</h4><div class="schedule-lessons-list">')
                            for lesson in lessons_by_day[day_key]:
                                lesson_type_class = f'lesson-type-{lesson["type"]}'
                                room_html = f'<span class="schedule-lesson-room">{lesson["room"]}</span>' if lesson['room'] else ''
                                html_parts.append(f'<div class="schedule-lesson-card {lesson_type_class}"><div class="schedule-lesson-time">{lesson["time"]}</div><div class="schedule-lesson-details"><span class="schedule-lesson-subject">{lesson["subject"]}</span><span class="schedule-lesson-teacher">{lesson["teacher"]}</span>{room_html}</div></div>')
                            html_parts.append('</div></div>')
                    html_parts.append('</div>')
                html_parts.append('<script>document.querySelectorAll(".schedule-group-select").forEach(sel=>{sel.addEventListener("change",function(){let id=this.id.replace("schedule-group-select-","");document.querySelectorAll(`[id^="group-${id}-"]`).forEach((c,i)=>{c.style.display=i==this.value?"block":"none"});let grp=document.querySelector(`#group-${id}-${this.value}`);if(grp){grp.querySelectorAll(".day-btn-inner").forEach(b=>b.classList.remove("active"));let allBtn=grp.querySelector(".day-btn-inner[data-day=\'all\']");if(allBtn)allBtn.classList.add("active");filterDaysInGroup(id,this.value,"all")}})});function filterDaysInGroup(uid,gidx,day){let grp=document.querySelector(`#group-${uid}-${gidx}`);if(!grp)return;grp.querySelectorAll(".schedule-day-section").forEach(s=>{s.style.display=(day==="all"||s.dataset.day===day)?"block":"none"});}document.querySelectorAll(".day-btn-inner").forEach(btn=>{btn.addEventListener("click",function(e){e.preventDefault();let parent=this.closest(".schedule-group-container");let gidx=parent.id.split("-").pop();let uid=parent.id.replace(`group-`,"").replace(`-${gidx}`,"");document.querySelectorAll(`#group-${uid}-${gidx} .day-btn-inner`).forEach(b=>b.classList.remove("active"));this.classList.add("active");filterDaysInGroup(uid,gidx,this.dataset.day)})});document.querySelectorAll(".schedule-group-container").forEach((c,i)=>{if(i===0)filterDaysInGroup(c.id.split("-")[1],0,"all")});</script>')
                return "".join(html_parts)
            return read_excel_simple(filepath)
        except Exception as e:
            return f"<div class='schedule-error'>Ошибка чтения Excel: {str(e)}</div>"
    
    def read_excel_simple(filepath):
        try:
            excel_file = pd.ExcelFile(filepath)
            html_parts = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                html_parts.append(f'<div class="schedule-excel-sheet"><h3 class="schedule-sheet-title">{sheet_name}</h3><div class="schedule-readable-content">')
                for idx, row in df.iterrows():
                    if row.isna().all():
                        continue
                    cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
                    if len(cells) >= 3:
                        lesson_type = 'practice'
                        subject_lower = cells[1].lower() if len(cells) > 1 else ''
                        if 'лекц' in subject_lower:
                            lesson_type = 'lecture'
                        elif 'лаб' in subject_lower:
                            lesson_type = 'lab'
                        elif 'экзам' in subject_lower:
                            lesson_type = 'exam'
                        html_parts.append(f'<div class="schedule-lesson-card" data-type="{lesson_type}"><div class="schedule-lesson-time">{cells[0]}</div><div class="schedule-lesson-details"><span class="schedule-lesson-subject">{cells[1]}</span><span class="schedule-lesson-teacher">{cells[2]}</span>{f"<span class=\"schedule-lesson-room\">{cells[3]}</span>" if len(cells) > 3 else ""}</div></div>')
                    elif len(cells) == 2:
                        html_parts.append(f'<div class="schedule-info-row"><strong>{cells[0]}:</strong> {cells[1]}</div>')
                    else:
                        html_parts.append(f"<p class='schedule-text-line'>{cells[0]}</p>")
                html_parts.append("</div></div>")
            return "".join(html_parts)
        except Exception as e:
            return f"<div class='schedule-error'>Ошибка чтения Excel: {str(e)}</div>"

    def get_pdf_page_count(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        try:
            with pdfplumber.open(filepath) as pdf:
                return len(pdf.pages)
        except:
            return 0

    def get_pdf_page_text(filename, page_num):
        filepath = os.path.join(RASP_FOLDER, filename)
        try:
            if not os.path.exists(filepath):
                return f"Файл не найден: {filename}"
            with pdfplumber.open(filepath) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    return text if text else "Страница пуста"
                else:
                    return f"Страница {page_num + 1} не существует. Всего страниц: {len(pdf.pages)}"
        except Exception as e:
            return f"Ошибка загрузки страницы: {str(e)}"

    def format_file_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} Б"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} КБ"
        else:
            return f"{size_bytes/(1024*1024):.1f} МБ"

    def get_file_icon(ext):
        icons = {'.pdf': '📄', '.xls': '📊', '.xlsx': '📊', '.doc': '📝', '.docx': '📝'}
        return icons.get(ext.lower(), '📁')

    # ==================== ДИНАМИЧЕСКИЕ СТРАНИЦЫ ИЗ PAGES_DATA ====================
    @app.route('/new/<slug>')
    def dynamic_page(slug):
        """Страницы из pages_data.py (статический контент)"""
        if slug not in PAGES:
            abort(404)
        
        page_data = PAGES[slug]
        
        # Создаём объект-заглушку для совместимости с шаблонами
        class PageObj:
            pass
        
        page = PageObj()
        page.slug = slug
        page.title = page_data['title']
        page.content = page_data['content']
        page.template = page_data['template']
        page.parent_id = None
        page.meta_description = page_data.get('meta_description', '')
        page.published = True
        
        children = []
        
        return render_template(f'dynamic/{page.template}.html', page=page, children=children)

    @app.route('/institutes')
    def institutes_page():
        """Страница со списком институтов (только те, у кого template='institute')"""
        institutes = [PAGES[slug] for slug in PAGES if PAGES[slug]['template'] == 'institute']
        # Добавляем slug к каждому институту
        for slug in PAGES:
            if PAGES[slug]['template'] == 'institute':
                for inst in institutes:
                    if inst['title'] == PAGES[slug]['title']:
                        inst['slug'] = slug
        return render_template('dynamic/institutes_page.html', institutes=institutes)

    # ==================== МАРШРУТЫ АДМИН ПАНЕЛИ (только для программ и новостей) ====================
    @app.route('/admin/programs')
    @login_required
    def admin_programs():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return render_template('admin_programs.html')

    @app.route('/admin/news')
    @login_required
    def admin_news():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return render_template('admin_news.html')

    @app.route('/admin/messages')
    @login_required
    def admin_messages():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return render_template('admin_messages.html')

    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return render_template('admin.html', all_pages=[])

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
                    'size_bytes': os.path.getsize(filepath), 'ext': ext, 'icon': get_file_icon(ext),
                    'url': url_for('schedule_view', filename=f)
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
                                 content=content, file_size=file_size, ext=ext)
        elif ext == '.pdf':
            total_pages = get_pdf_page_count(filename)
            return render_template('schedule_pdf_improved.html', filename=filename, file_title=config['title'],
                                 file_description=config['description'], file_institute=config['institute'],
                                 total_pages=total_pages, file_size=file_size, ext=ext)
        else:
            flash('Неподдерживаемый формат файла', 'warning')
            return redirect(url_for('schedule_list'))

    @app.route('/api/pdf/page')
    def api_pdf_page():
        filename = request.args.get('file')
        page = request.args.get('page', 0, type=int)
        if not filename:
            return jsonify({'error': 'No filename', 'text': '', 'success': False}), 400
        try:
            text = get_pdf_page_text(filename, page)
            return jsonify({'page': page, 'text': text, 'success': True})
        except Exception as e:
            return jsonify({'error': str(e), 'text': f'Ошибка загрузки страницы: {str(e)}', 'success': False}), 500

    @app.route('/api/schedule/<path:filename>')
    def api_schedule_data(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found', 'lessons': []}), 404
        ext = os.path.splitext(filename)[1].lower()
        lessons = []
        if ext in ['.xls', '.xlsx']:
            try:
                excel_file = pd.ExcelFile(filepath)
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                    for idx, row in df.iterrows():
                        if row.isna().all():
                            continue
                        cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
                        if len(cells) >= 3:
                            lesson_type = 'practice'
                            subject_lower = cells[1].lower() if len(cells) > 1 else ''
                            if 'лекц' in subject_lower:
                                lesson_type = 'lecture'
                            elif 'лаб' in subject_lower:
                                lesson_type = 'lab'
                            elif 'экзам' in subject_lower:
                                lesson_type = 'exam'
                            lessons.append({
                                'time': cells[0], 'subject': cells[1], 'teacher': cells[2],
                                'room': cells[3] if len(cells) > 3 else '', 'type': lesson_type, 'sheet': sheet_name
                            })
            except Exception as e:
                return jsonify({'error': str(e), 'lessons': []}), 500
        return jsonify({'lessons': lessons, 'total': len(lessons)})

    # ==================== ДИНАМИЧЕСКИЙ ПОИСК ====================
    @app.route('/api/search')
    def api_search():
        query = request.args.get('q', '').strip().lower()
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        results = []
        seen_urls = set()
        
        # 1. Поиск по статическим страницам (из PAGES)
        for slug, page_data in PAGES.items():
            if query in page_data['title'].lower() or (page_data.get('meta_description') and query in page_data['meta_description'].lower()):
                url = url_for('dynamic_page', slug=slug)
                if url not in seen_urls:
                    seen_urls.add(url)
                    type_ru = {
                        'institute': 'Институт',
                        'department': 'Кафедра',
                        'info_page': 'Страница',
                        'student_section': 'Раздел',
                        'applicant_section': 'Раздел',
                        'science_section': 'Раздел'
                    }.get(page_data['template'], 'Страница')
                    
                    results.append({
                        'type': page_data['template'],
                        'type_ru': type_ru,
                        'title': page_data['title'],
                        'url': url,
                        'description': page_data.get('meta_description', type_ru),
                        'icon': get_icon_for_template(page_data['template'])
                    })
        
        # 2. Поиск по программам обучения
        programs = Program.query.filter(
            db.or_(
                Program.name.ilike(f'%{query}%'),
                Program.description.ilike(f'%{query}%'),
                Program.degree.ilike(f'%{query}%')
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
        
        # 3. Поиск по новостям
        news = News.query.filter(
            db.or_(
                News.title.ilike(f'%{query}%'),
                News.content.ilike(f'%{query}%')
            )
        ).order_by(News.published_at.desc()).limit(5).all()
        
        for n in news:
            url = url_for('news')
            if url not in seen_urls:
                seen_urls.add(url)
                date_str = n.published_at.strftime('%d.%m.%Y') if n.published_at else ''
                results.append({
                    'type': 'news',
                    'type_ru': 'Новость',
                    'title': n.title,
                    'url': url,
                    'description': f'{date_str} • {n.content[:100]}...',
                    'icon': '📰'
                })
        
        # 4. Поиск по расписанию
        for f in os.listdir(RASP_FOLDER):
            filepath = os.path.join(RASP_FOLDER, f)
            if os.path.isfile(filepath) and query in f.lower():
                config = SCHEDULE_CONFIG.get(f, {'title': f, 'description': 'Расписание занятий', 'institute': 'Другое'})
                url = url_for('schedule_view', filename=f)
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        'type': 'schedule',
                        'type_ru': 'Расписание',
                        'title': config['title'],
                        'url': url,
                        'description': f"{config['institute']} • {config['description']}",
                        'icon': '📅'
                    })
        
        results = results[:25]
        return jsonify({'results': results})

    def get_icon_for_template(template):
        icons = {
            'institute': '🏛️',
            'department': '📚',
            'info_page': '📄',
            'student_section': '👨‍🎓',
            'applicant_section': '📝',
            'science_section': '🔬'
        }
        return icons.get(template, '📄')

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return render_template('search.html', query=query, all_results=[], total_results=0)
        
        results = []
        seen_urls = set()
        
        # Поиск по статическим страницам
        for slug, page_data in PAGES.items():
            if query.lower() in page_data['title'].lower():
                url = url_for('dynamic_page', slug=slug)
                if url not in seen_urls:
                    seen_urls.add(url)
                    type_ru = {
                        'institute': 'Институт',
                        'department': 'Кафедра',
                        'info_page': 'Страница',
                        'student_section': 'Раздел',
                        'applicant_section': 'Раздел',
                        'science_section': 'Раздел'
                    }.get(page_data['template'], 'Страница')
                    
                    results.append({
                        'type': page_data['template'],
                        'type_ru': type_ru,
                        'title': page_data['title'],
                        'url': url,
                        'description': type_ru,
                        'content_preview': page_data['content'][:200] + '...' if len(page_data['content']) > 200 else page_data['content']
                    })
        
        # Поиск по программам
        programs = Program.query.filter(
            db.or_(
                Program.name.ilike(f'%{query}%'),
                Program.description.ilike(f'%{query}%'),
                Program.degree.ilike(f'%{query}%')
            )
        ).all()
        
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
                    'content_preview': p.description[:200] + '...' if len(p.description) > 200 else p.description
                })
        
        # Поиск по новостям
        news = News.query.filter(
            db.or_(
                News.title.ilike(f'%{query}%'),
                News.content.ilike(f'%{query}%')
            )
        ).order_by(News.published_at.desc()).all()
        
        for n in news:
            url = url_for('news')
            if url not in seen_urls:
                seen_urls.add(url)
                date_str = n.published_at.strftime('%d.%m.%Y') if n.published_at else ''
                results.append({
                    'type': 'news',
                    'type_ru': 'Новость',
                    'title': n.title,
                    'url': url,
                    'description': f'{date_str}',
                    'content_preview': n.content[:200] + '...' if len(n.content) > 200 else n.content
                })
        
        # Поиск по расписанию
        for f in os.listdir(RASP_FOLDER):
            filepath = os.path.join(RASP_FOLDER, f)
            if os.path.isfile(filepath) and query.lower() in f.lower():
                config = SCHEDULE_CONFIG.get(f, {'title': f, 'description': 'Расписание занятий', 'institute': 'Другое'})
                url = url_for('schedule_view', filename=f)
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        'type': 'schedule',
                        'type_ru': 'Расписание',
                        'title': config['title'],
                        'url': url,
                        'description': f"{config['institute']}",
                        'content_preview': config['description']
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

    # ==================== РЕДИРЕКТЫ НА ДИНАМИЧЕСКИЕ СТРАНИЦЫ ====================
    redirect_routes = [
        ('/university-today', 'university_today'), ('/structure', 'structure'), ('/leadership', 'leadership'),
        ('/academic-council', 'academic_council'), ('/departments', 'departments'), ('/library', 'library'),
        ('/educational-activity', 'educational_activity'), ('/professionalitet', 'professionalitet'),
        ('/inclusive-education', 'inclusive_education'), ('/additional-education', 'additional_education'),
        ('/science', 'science'), ('/science-news', 'science_news'), ('/laboratories', 'laboratories'),
        ('/science-schools', 'science_schools'), ('/grants', 'grants'), ('/conferences', 'conferences'),
        ('/volunteer', 'volunteer'), ('/dormitory', 'dormitory'), ('/payment', 'payment'),
        ('/cossack', 'cossack'), ('/international-students', 'international_students'),
        ('/school-info', 'school_info'), ('/school-news', 'school_news'), ('/school-conferences', 'school_conferences'),
        ('/school-awards', 'school_awards'), ('/olympiads', 'olympiads'), ('/preparatory-courses', 'preparatory_courses'),
        ('/agro-classes', 'agro_classes'), ('/career-guidance', 'career_guidance'), ('/admission-info', 'admission_info'),
        ('/admission-addresses', 'admission_addresses'), ('/admission-faq', 'admission_faq'), ('/admission-docs', 'admission_docs'),
        ('/admission-info-detail', 'admission_info_detail'), ('/disabled-info', 'disabled_info'),
        ('/competition-lists', 'competition_lists'), ('/paid-education', 'paid_education'), ('/entrance-tests', 'entrance_tests'),
        ('/enrollment-orders', 'enrollment_orders'), ('/postgraduate', 'postgraduate'), ('/doctoral', 'doctoral'),
        ('/attestation', 'attestation'), ('/candidate-exams', 'candidate_exams'), ('/dissertations', 'dissertations'),
        ('/science-supervisors', 'science_supervisors'), ('/employee', 'employee'), ('/employer', 'employer'),
        ('/alumni', 'alumni'), ('/contacts-departments', 'contacts_departments'), ('/international', 'international'),
        ('/university-life', 'university_life'), ('/institute/agro', 'institute_agro'), ('/institute/biotech', 'institute_biotech'),
        ('/institute/economy', 'institute_economy'), ('/institute/engineering', 'institute_engineering'),
        ('/institute/food', 'institute_food'), ('/institute/land', 'institute_land'), ('/institute/law', 'institute_law'),
        ('/institute/achinsk', 'institute_achinsk'), ('/student/council', 'student_council'),
        ('/student/teams', 'student_teams'), ('/student/culture', 'student_culture'), ('/student/sports', 'student_sports'),
        ('/student/psychologist', 'student_psychologist'), ('/student/social-support', 'student_social_support'),
        ('/student/projects', 'student_projects'), ('/student/faq', 'student_faq'), ('/student/calendar', 'student_calendar'),
        ('/student/scholarships', 'student_scholarships'), ('/student/regulations', 'student_regulations'),
        ('/student/educational-resources', 'student_educational_resources'), ('/student/mass-courses', 'student_mass_courses'),
        ('/student/textbooks', 'student_textbooks'), ('/student/practice-bases', 'student_practice_bases'),
        ('/student/practice-dates', 'student_practice_dates'), ('/student/practice-docs', 'student_practice_docs'),
        ('/student/practice-survey', 'student_practice_survey'), ('/student/practice-instruction', 'student_practice_instruction'),
        ('/student/practice-requests', 'student_practice_requests'), ('/student/survey', 'student_survey'),
        ('/student/international-assoc', 'student_international_assoc'), ('/university', 'university_main'),
        ('/university/history', 'university_history'), ('/university/association', 'university_association'),
        ('/university/profsoyuz', 'university_profsoyuz'), ('/university/press', 'university_press'),
        ('/university/press-center', 'university_press_center'), ('/university/brandbook', 'university_brandbook'),
        ('/university/vesti', 'university_vesti'), ('/university/media-about-us', 'university_media_about_us'),
        ('/university/prosecutor', 'university_prosecutor'), ('/university/quality-management', 'university_quality_management'),
        ('/university/endowment', 'university_endowment'), ('/university/driving-school', 'university_driving_school'),
        ('/university/jalinga', 'university_jalinga'), ('/applicant', 'applicant_main'),
        ('/target-education', 'target_education'), ('/bonuses', 'bonuses'), ('/enrollment-info', 'enrollment_info'),
        ('/applicant-lists', 'applicant_lists'), ('/postgraduate-admission', 'postgraduate_admission'),
        ('/doctoral-admission', 'doctoral_admission'), ('/admission-regulations', 'admission_regulations'),
        ('/exam-schedule', 'exam_schedule'), ('/admission-committee', 'admission_committee')
    ]
    
    for route_path, slug in redirect_routes:
        def make_redirect(slug_name):
            return lambda: redirect(url_for('dynamic_page', slug=slug_name), code=301)
        app.add_url_rule(route_path, f'redirect_{slug}', make_redirect(slug))

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

    # ==================== РЕДИРЕКТЫ ДЛЯ СТАРЫХ HTML СТРАНИЦ ====================
    @app.route('/<old_slug>.html')
    def redirect_old_pages(old_slug):
        if old_slug in PAGES:
            return redirect(url_for('dynamic_page', slug=old_slug), code=301)
        flash('Страница не найдена', 'danger')
        return redirect(url_for('index'))
    
    @app.route('/student')
    def student_redirect():
        return redirect(url_for('dynamic_page', slug='student_main'), code=301)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)