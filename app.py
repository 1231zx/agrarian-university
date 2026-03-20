from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_caching import Cache
from config import Config
from models import db, User, Program, News, Contact, PageContent
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

    # Инициализация расширений
    db.init_app(app)
    CORS(app)
    
    # Инициализация почты и кеша
    mail = Mail(app)
    cache = Cache(app)
    
    # Инициализация Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Добавляем контекстный процессор для current_user
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    # Импортируем и инициализируем API после создания app
    from api import init_api
    init_api(app)

    # Проверка подключения к БД
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ Подключение к PostgreSQL успешно!")
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")

    # Папка с файлами расписания
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
        'CPSSZ2.xls': {
            'title': 'ЦПССЗ - все курсы',
            'description': 'Расписание для Центра подготовки специалистов среднего звена (1-4 курсы)',
            'institute': 'ЦПССЗ'
        },
        'IAT2.xls': {
            'title': 'ИАЭТ - все курсы',
            'description': 'Институт агроэкологических технологий (1-4 курсы)',
            'institute': 'ИАЭТ'
        },
        'IEU2.xls': {
            'title': 'ИЭиУ АПК - все курсы',
            'description': 'Институт экономики и управления АПК (1-4 курсы)',
            'institute': 'ИЭиУ АПК'
        },
        'IEUv2.xls': {
            'title': 'ИЭиУ АПК - вечернее отделение',
            'description': 'Институт экономики и управления АПК, вечерняя форма',
            'institute': 'ИЭиУ АПК'
        },
        'IiSiE2.xlsx': {
            'title': 'ИИСиЭ - расписание',
            'description': 'Институт информационных систем и инженерии',
            'institute': 'ИИСиЭ'
        },
        'IPBVM2.xls': {
            'title': 'ИПБиВМ - все курсы',
            'description': 'Институт прикладной биотехнологии и ветеринарной медицины',
            'institute': 'ИПБиВМ'
        },
        'IPP2.xls': {
            'title': 'ИПП - все курсы',
            'description': 'Институт пищевых производств',
            'institute': 'ИПП'
        },
        'IZKP2.xls': {
            'title': 'ИЗКиП - все курсы',
            'description': 'Институт землеустройства, кадастров и природообустройства',
            'institute': 'ИЗКиП'
        },
        'UI2.xlsx': {
            'title': 'Юридический институт - расписание',
            'description': 'Юридический институт',
            'institute': 'ЮИ'
        },
        'UIv2.xlsx': {
            'title': 'Юридический институт - вечернее отделение',
            'description': 'Юридический институт, вечерняя форма',
            'institute': 'ЮИ'
        }
    }

    # ==================== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ====================
    def read_excel_file(filename):
        """Читает Excel файл и форматирует в читаемый вид с группировкой по группам"""
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
                            'time': cells[0],
                            'subject': cells[1],
                            'teacher': cells[2] if len(cells) > 2 else '',
                            'room': cells[3] if len(cells) > 3 else '',
                            'type': lesson_type,
                            'day': day_of_week
                        })
                
                if lessons:
                    if group_name not in groups:
                        groups[group_name] = []
                    groups[group_name].extend(lessons)
            
            if groups:
                unique_id = filename.replace('.', '_').replace(' ', '_').replace('-', '_')
                
                html_parts.append(f"""
                <div class="schedule-group-selector" data-unique="{unique_id}">
                    <label>👥 Выберите группу:</label>
                    <select id="schedule-group-select-{unique_id}" class="schedule-group-select">
                """)
                
                for i, group_name in enumerate(groups.keys()):
                    selected = 'selected' if i == 0 else ''
                    html_parts.append(f'<option value="{i}" {selected}>{group_name}</option>')
                
                html_parts.append(f"""
                    </select>
                </div>
                """)
                
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
                    html_parts.append(f'<h3 class="schedule-group-title">📚 {group_name}</h3>')
                    
                    html_parts.append(f"""
                    <div class="schedule-day-switcher-inner" data-group="{i}">
                        <button class="day-btn-inner active" data-day="all">📅 Все дни</button>
                        <button class="day-btn-inner" data-day="mon">ПН</button>
                        <button class="day-btn-inner" data-day="tue">ВТ</button>
                        <button class="day-btn-inner" data-day="wed">СР</button>
                        <button class="day-btn-inner" data-day="thu">ЧТ</button>
                        <button class="day-btn-inner" data-day="fri">ПТ</button>
                        <button class="day-btn-inner" data-day="sat">СБ</button>
                    </div>
                    """)
                    
                    day_names = {
                        'mon': 'Понедельник',
                        'tue': 'Вторник',
                        'wed': 'Среда',
                        'thu': 'Четверг',
                        'fri': 'Пятница',
                        'sat': 'Суббота',
                        'unknown': 'Другое'
                    }
                    
                    for day_key, day_name in day_names.items():
                        if lessons_by_day.get(day_key) and len(lessons_by_day[day_key]) > 0:
                            html_parts.append(f'<div class="schedule-day-section" data-day="{day_key}">')
                            html_parts.append(f'<h4 class="schedule-day-title">{day_name}</h4>')
                            html_parts.append('<div class="schedule-lessons-list">')
                            for lesson in lessons_by_day[day_key]:
                                lesson_type_class = f'lesson-type-{lesson["type"]}'
                                room_html = f'<span class="schedule-lesson-room">{lesson["room"]}</span>' if lesson['room'] else ''
                                html_parts.append(f'''
                                    <div class="schedule-lesson-card {lesson_type_class}">
                                        <div class="schedule-lesson-time">{lesson['time']}</div>
                                        <div class="schedule-lesson-details">
                                            <span class="schedule-lesson-subject">{lesson['subject']}</span>
                                            <span class="schedule-lesson-teacher">{lesson['teacher']}</span>
                                            {room_html}
                                        </div>
                                    </div>
                                ''')
                            html_parts.append('</div></div>')
                    html_parts.append('</div>')
                
                html_parts.append(f"""
                <script>
                (function() {{
                    const uniqueId = '{unique_id}';
                    const groupSelect = document.getElementById('schedule-group-select-' + uniqueId);
                    const groupContainers = document.querySelectorAll('[id^="group-' + uniqueId + '-"]');
                    let currentGroup = 0;
                    function filterDaysInGroup(groupIndex, day) {{
                        const groupContainer = document.getElementById('group-' + uniqueId + '-' + groupIndex);
                        if (!groupContainer) return;
                        const daySections = groupContainer.querySelectorAll('.schedule-day-section');
                        daySections.forEach(section => {{
                            const sectionDay = section.dataset.day;
                            if (day === 'all' || sectionDay === day) {{
                                section.style.display = 'block';
                            }} else {{
                                section.style.display = 'none';
                            }}
                        }});
                    }}
                    if (groupSelect) {{
                        groupSelect.addEventListener('change', function() {{
                            const newGroup = parseInt(this.value);
                            currentGroup = newGroup;
                            groupContainers.forEach((container, idx) => {{
                                container.style.display = idx === newGroup ? 'block' : 'none';
                            }});
                            const activeGroupContainer = document.getElementById('group-' + uniqueId + '-' + newGroup);
                            if (activeGroupContainer) {{
                                const dayBtns = activeGroupContainer.querySelectorAll('.day-btn-inner');
                                dayBtns.forEach(btn => btn.classList.remove('active'));
                                const allBtn = activeGroupContainer.querySelector('.day-btn-inner[data-day="all"]');
                                if (allBtn) allBtn.classList.add('active');
                            }}
                            filterDaysInGroup(newGroup, 'all');
                        }});
                    }}
                    groupContainers.forEach((container, groupIdx) => {{
                        const dayBtns = container.querySelectorAll('.day-btn-inner');
                        dayBtns.forEach(btn => {{
                            btn.addEventListener('click', function(e) {{
                                e.preventDefault();
                                e.stopPropagation();
                                dayBtns.forEach(b => b.classList.remove('active'));
                                this.classList.add('active');
                                filterDaysInGroup(groupIdx, this.dataset.day);
                            }});
                        }});
                    }});
                    filterDaysInGroup(0, 'all');
                }})();
                </script>
                """)
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
                html_parts.append(f"""
                    <div class="schedule-excel-sheet">
                        <h3 class="schedule-sheet-title">📋 {sheet_name}</h3>
                        <div class="schedule-readable-content">
                """)
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
                        html_parts.append(f"""
                            <div class="schedule-lesson-card" data-type="{lesson_type}">
                                <div class="schedule-lesson-time">{cells[0]}</div>
                                <div class="schedule-lesson-details">
                                    <span class="schedule-lesson-subject">{cells[1]}</span>
                                    <span class="schedule-lesson-teacher">{cells[2]}</span>
                                    {f'<span class="schedule-lesson-room">{cells[3]}</span>' if len(cells) > 3 else ''}
                                </div>
                            </div>
                        """)
                    elif len(cells) == 2:
                        html_parts.append(f"""
                            <div class="schedule-info-row">
                                <strong>{cells[0]}:</strong> {cells[1]}
                            </div>
                        """)
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
        
        keywords = {
            'расписание': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'занятие': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'урок': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'пара': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'экзамен': {'url': 'schedule_list', 'title': '📝 Расписание экзаменов', 'description': 'Расписание вступительных испытаний и экзаменов'},
        }
        for keyword, data in keywords.items():
            if keyword in query:
                url = url_for(data['url'])
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({'type': 'schedule_main', 'type_ru': '📅 Расписание', 'title': data['title'], 'url': url, 'description': data['description'], 'icon': '📅'})
                break
        
        programs = Program.query.filter(db.or_(Program.name.ilike(f'%{query}%'), Program.description.ilike(f'%{query}%'), Program.degree.ilike(f'%{query}%'))).limit(3).all()
        for p in programs:
            url = url_for('program_detail', program_id=p.id)
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({'type': 'program', 'type_ru': 'Программа', 'title': p.name, 'url': url, 'description': f"{p.degree} • {p.duration}", 'icon': '📚'})
        
        news = News.query.filter(db.or_(News.title.ilike(f'%{query}%'), News.content.ilike(f'%{query}%'))).order_by(News.published_at.desc()).limit(3).all()
        for n in news:
            url = url_for('news')
            if url not in seen_urls:
                seen_urls.add(url)
                date_str = n.published_at.strftime('%d.%m.%Y') if n.published_at else ''
                results.append({'type': 'news', 'type_ru': 'Новость', 'title': n.title, 'url': url, 'description': f"{date_str} • {n.content[:100]}...", 'icon': '📰'})
        
        for f in os.listdir(RASP_FOLDER):
            filepath = os.path.join(RASP_FOLDER, f)
            if os.path.isfile(filepath) and query in f.lower():
                config = SCHEDULE_CONFIG.get(f, {'title': f, 'description': 'Расписание занятий', 'institute': 'Другое'})
                url = url_for('schedule_view', filename=f)
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({'type': 'schedule', 'type_ru': 'Расписание', 'title': config['title'], 'url': url, 'description': f"{config['institute']} • {config['description']}", 'icon': '📅'})
        
        results = results[:15]
        return jsonify({'results': results})

    @app.route('/search')
    def search():
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return render_template('search.html', query=query, all_results=[], total_results=0)
        results = []
        seen_urls = set()
        
        keywords = {
            'расписание': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'занятие': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'урок': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'пара': {'url': 'schedule_list', 'title': '📅 Расписание занятий', 'description': 'Все расписания по институтам и курсам'},
            'экзамен': {'url': 'schedule_list', 'title': '📝 Расписание экзаменов', 'description': 'Расписание вступительных испытаний и экзаменов'},
        }
        for keyword, data in keywords.items():
            if keyword in query.lower():
                url = url_for(data['url'])
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({'type': 'schedule_main', 'type_ru': '📅 Расписание', 'title': data['title'], 'url': url, 'description': data['description']})
                break
        
        programs = Program.query.filter(db.or_(Program.name.ilike(f'%{query}%'), Program.description.ilike(f'%{query}%'), Program.degree.ilike(f'%{query}%'))).all()
        for p in programs:
            url = url_for('program_detail', program_id=p.id)
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({'type': 'program', 'type_ru': 'Программа', 'title': p.name, 'url': url, 'description': f"{p.degree} • {p.duration} • {p.description[:200]}..."})
        
        news = News.query.filter(db.or_(News.title.ilike(f'%{query}%'), News.content.ilike(f'%{query}%'))).order_by(News.published_at.desc()).all()
        for n in news:
            url = url_for('news')
            if url not in seen_urls:
                seen_urls.add(url)
                date_str = n.published_at.strftime('%d.%m.%Y') if n.published_at else ''
                results.append({'type': 'news', 'type_ru': 'Новость', 'title': n.title, 'url': url, 'description': f"{date_str} • {n.content[:200]}..."})
        
        for f in os.listdir(RASP_FOLDER):
            filepath = os.path.join(RASP_FOLDER, f)
            if os.path.isfile(filepath) and query.lower() in f.lower():
                config = SCHEDULE_CONFIG.get(f, {'title': f, 'description': 'Расписание занятий', 'institute': 'Другое'})
                url = url_for('schedule_view', filename=f)
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({'type': 'schedule', 'type_ru': 'Расписание', 'title': config['title'], 'url': url, 'description': f"{config['institute']} • {config['description']}"})
        
        return render_template('search.html', query=query, all_results=results, total_results=len(results))

    # ==================== СТАТИЧЕСКИЕ СТРАНИЦЫ (HTML) ====================
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

    @app.route('/university-today')
    def university_today():
        return render_template('university_today.html')

    @app.route('/structure')
    def structure():
        return render_template('structure.html')

    @app.route('/leadership')
    def leadership():
        return render_template('leadership.html')

    @app.route('/academic-council')
    def academic_council():
        return render_template('academic_council.html')

    @app.route('/departments')
    def departments():
        return render_template('departments.html')

    @app.route('/library')
    def library():
        return render_template('library.html')

    @app.route('/educational-activity')
    def educational_activity():
        return render_template('educational_activity.html')

    @app.route('/professionalitet')
    def professionalitet():
        return render_template('professionalitet.html')

    @app.route('/inclusive-education')
    def inclusive_education():
        return render_template('inclusive_education.html')

    @app.route('/additional-education')
    def additional_education():
        return render_template('additional_education.html')

    @app.route('/science')
    def science():
        return render_template('science.html')

    @app.route('/science-news')
    def science_news():
        return render_template('science_news.html')

    @app.route('/laboratories')
    def laboratories():
        return render_template('laboratories.html')

    @app.route('/science-schools')
    def science_schools():
        return render_template('science_schools.html')

    @app.route('/grants')
    def grants():
        return render_template('grants.html')

    @app.route('/conferences')
    def conferences():
        return render_template('conferences.html')

    @app.route('/student-news')
    def student_news():
        return render_template('school_news.html')

    @app.route('/student-council')
    def student_council():
        return render_template('student_teams.html')

    @app.route('/student-teams')
    def student_teams():
        return render_template('student_teams.html')

    @app.route('/volunteer')
    def volunteer():
        return render_template('volunteer.html')

    @app.route('/dormitory')
    def dormitory():
        return render_template('dormitory.html')

    @app.route('/payment')
    def payment():
        return render_template('payment.html')

    @app.route('/cossack')
    def cossack():
        return render_template('cossack.html')

    @app.route('/international-students')
    def international_students():
        return render_template('international_students.html')

    @app.route('/school-info')
    def school_info():
        return render_template('school_info.html')

    @app.route('/school-news')
    def school_news():
        return render_template('school_news.html')

    @app.route('/school-conferences')
    def school_conferences():
        return render_template('school_conferences.html')

    @app.route('/school-awards')
    def school_awards():
        return render_template('school_awards.html')

    @app.route('/olympiads')
    def olympiads():
        return render_template('olympiads.html')

    @app.route('/preparatory-courses')
    def preparatory_courses():
        return render_template('preparatory_courses.html')

    @app.route('/agro-classes')
    def agro_classes():
        return render_template('agro_classes.html')

    @app.route('/career-guidance')
    def career_guidance():
        return render_template('career_guidance.html')

    @app.route('/admission-info')
    def admission_info():
        return render_template('admission_info.html')

    @app.route('/admission-addresses')
    def admission_addresses():
        return render_template('admission_addresses.html')

    @app.route('/admission-faq')
    def admission_faq():
        return render_template('admission_faq.html')

    @app.route('/admission-docs')
    def admission_docs():
        return render_template('admission_docs.html')

    @app.route('/admission-info-detail')
    def admission_info_detail():
        return render_template('admission_info_detail.html')

    @app.route('/disabled-info')
    def disabled_info():
        return render_template('disabled_info.html')

    @app.route('/competition-lists')
    def competition_lists():
        return render_template('competition_lists.html')

    @app.route('/paid-education')
    def paid_education():
        return render_template('paid_education.html')

    @app.route('/entrance-tests')
    def entrance_tests():
        return render_template('entrance_tests.html')

    @app.route('/enrollment-orders')
    def enrollment_orders():
        return render_template('enrollment_orders.html')

    @app.route('/postgraduate')
    def postgraduate():
        return render_template('postgraduate.html')

    @app.route('/doctoral')
    def doctoral():
        return render_template('doctoral.html')

    @app.route('/attestation')
    def attestation():
        return render_template('attestation.html')

    @app.route('/candidate-exams')
    def candidate_exams():
        return render_template('candidate_exams.html')

    @app.route('/dissertations')
    def dissertations():
        return render_template('dissertations.html')

    @app.route('/science-supervisors')
    def science_supervisors():
        return render_template('science_supervisors.html')

    @app.route('/employee')
    def employee():
        return render_template('employee.html')

    @app.route('/employer')
    def employer():
        return render_template('employer.html')

    @app.route('/alumni')
    def alumni():
        return render_template('alumni.html')

    @app.route('/contacts-departments')
    def contacts_departments():
        return render_template('contacts_departments.html')

    @app.route('/international')
    def international():
        return render_template('international.html')

    @app.route('/university-life')
    def university_life():
        return render_template('university_life.html')

    # ==================== МАРШРУТЫ ИНСТИТУТОВ ====================
    @app.route('/institute/agro')
    def institute_agro():
        return render_template('institute_agro.html')

    @app.route('/institute/agro/department/agronomy')
    def institute_agro_department_agronomy():
        return render_template('institute_agro_department_agronomy.html')

    @app.route('/institute/agro/department/plant_breeding')
    def institute_agro_department_plant_breeding():
        return render_template('institute_agro_department_plant_breeding.html')

    @app.route('/institute/agro/department/soil')
    def institute_agro_department_soil():
        return render_template('institute_agro_department_soil.html')

    @app.route('/institute/agro/department/landscape')
    def institute_agro_department_landscape():
        return render_template('institute_agro_department_landscape.html')

    @app.route('/institute/agro/department/ecology')
    def institute_agro_department_ecology():
        return render_template('institute_agro_department_ecology.html')

    @app.route('/institute/agro/department/physical_culture')
    def institute_agro_department_physical_culture():
        return render_template('institute_agro_department_physical_culture.html')

    @app.route('/institute/agro/department/languages')
    def institute_agro_department_languages():
        return render_template('institute_agro_department_languages.html')

    @app.route('/institute/biotech')
    def institute_biotech():
        return render_template('institute_biotech.html')

    @app.route('/institute/biotech/department/anatomy')
    def institute_biotech_department_anatomy():
        return render_template('institute_biotech_department_anatomy.html')

    @app.route('/institute/biotech/department/zootechny')
    def institute_biotech_department_zootechny():
        return render_template('institute_biotech_department_zootechny.html')

    @app.route('/institute/biotech/department/breeding')
    def institute_biotech_department_breeding():
        return render_template('institute_biotech_department_breeding.html')

    @app.route('/institute/biotech/department/internal_diseases')
    def institute_biotech_department_internal_diseases():
        return render_template('institute_biotech_department_internal_diseases.html')

    @app.route('/institute/biotech/department/epizootology')
    def institute_biotech_department_epizootology():
        return render_template('institute_biotech_department_epizootology.html')

    @app.route('/institute/economy')
    def institute_economy():
        return render_template('institute_economy.html')

    @app.route('/institute/economy/department/organization')
    def institute_economy_department_organization():
        return render_template('institute_economy_department_organization.html')

    @app.route('/institute/economy/department/management')
    def institute_economy_department_management():
        return render_template('institute_economy_department_management.html')

    @app.route('/institute/economy/department/information')
    def institute_economy_department_information():
        return render_template('institute_economy_department_information.html')

    @app.route('/institute/economy/department/accounting')
    def institute_economy_department_accounting():
        return render_template('institute_economy_department_accounting.html')

    @app.route('/institute/economy/department/psychology')
    def institute_economy_department_psychology():
        return render_template('institute_economy_department_psychology.html')

    @app.route('/institute/engineering')
    def institute_engineering():
        return render_template('institute_engineering.html')

    @app.route('/institute/engineering/department/physics')
    def institute_engineering_department_physics():
        return render_template('institute_engineering_department_physics.html')

    @app.route('/institute/engineering/department/mechanization')
    def institute_engineering_department_mechanization():
        return render_template('institute_engineering_department_mechanization.html')

    @app.route('/institute/engineering/department/general_engineering')
    def institute_engineering_department_general_engineering():
        return render_template('institute_engineering_department_general_engineering.html')

    @app.route('/institute/engineering/department/system_energy')
    def institute_engineering_department_system_energy():
        return render_template('institute_engineering_department_system_energy.html')

    @app.route('/institute/engineering/department/electrical_engineering')
    def institute_engineering_department_electrical_engineering():
        return render_template('institute_engineering_department_electrical_engineering.html')

    @app.route('/institute/engineering/department/tractors')
    def institute_engineering_department_tractors():
        return render_template('institute_engineering_department_tractors.html')

    @app.route('/institute/engineering/department/electrical_supply')
    def institute_engineering_department_electrical_supply():
        return render_template('institute_engineering_department_electrical_supply.html')

    @app.route('/institute/food')
    def institute_food():
        return render_template('institute_food.html')

    @app.route('/institute/food/department/bakery')
    def institute_food_department_bakery():
        return render_template('institute_food_department_bakery.html')

    @app.route('/institute/food/department/canning')
    def institute_food_department_canning():
        return render_template('institute_food_department_canning.html')

    @app.route('/institute/food/department/equipment')
    def institute_food_department_equipment():
        return render_template('institute_food_department_equipment.html')

    @app.route('/institute/food/department/quality')
    def institute_food_department_quality():
        return render_template('institute_food_department_quality.html')

    @app.route('/institute/food/department/chemistry')
    def institute_food_department_chemistry():
        return render_template('institute_food_department_chemistry.html')

    @app.route('/institute/land')
    def institute_land():
        return render_template('institute_land.html')

    @app.route('/institute/land/department/land_management')
    def institute_land_department_land_management():
        return render_template('institute_land_department_land_management.html')

    @app.route('/institute/land/department/gis')
    def institute_land_department_gis():
        return render_template('institute_land_department_gis.html')

    @app.route('/institute/land/department/environmental')
    def institute_land_department_environmental():
        return render_template('institute_land_department_environmental.html')

    @app.route('/institute/land/department/safety')
    def institute_land_department_safety():
        return render_template('institute_land_department_safety.html')

    @app.route('/institute/law')
    def institute_law():
        return render_template('institute_law.html')

    @app.route('/institute/law/department/theory')
    def institute_law_department_theory():
        return render_template('institute_law_department_theory.html')

    @app.route('/institute/law/department/civil')
    def institute_law_department_civil():
        return render_template('institute_law_department_civil.html')

    @app.route('/institute/law/department/criminal_procedure')
    def institute_law_department_criminal_procedure():
        return render_template('institute_law_department_criminal_procedure.html')

    @app.route('/institute/law/department/criminal_law')
    def institute_law_department_criminal_law():
        return render_template('institute_law_department_criminal_law.html')

    @app.route('/institute/law/department/land_law')
    def institute_law_department_land_law():
        return render_template('institute_law_department_land_law.html')

    @app.route('/institute/law/department/history')
    def institute_law_department_history():
        return render_template('institute_law_department_history.html')

    @app.route('/institute/law/department/philosophy')
    def institute_law_department_philosophy():
        return render_template('institute_law_department_philosophy.html')

    @app.route('/institute/law/department/forensic')
    def institute_law_department_forensic():
        return render_template('institute_law_department_forensic.html')

    @app.route('/institute/achinsk')
    def institute_achinsk():
        return render_template('institute_achinsk.html')

    @app.route('/institute/achinsk/department/law')
    def institute_achinsk_department_law():
        return render_template('institute_achinsk_department_law.html')

    @app.route('/institute/achinsk/department/engineering')
    def institute_achinsk_department_engineering():
        return render_template('institute_achinsk_department_engineering.html')

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
            flash('У вас нет прав доступа к этой странице.', 'danger')
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

    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin:
            flash('У вас нет прав доступа к этой странице.', 'danger')
            return redirect(url_for('index'))
        return render_template('admin.html')

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)