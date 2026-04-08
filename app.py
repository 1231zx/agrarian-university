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
        'IEUv2.xls': {'title': 'ИЭиУ АПК - вечернее отделение', 'description': 'Институт экономики и управления АПК, вечерняя форма', 'institute': 'ИЭиУ АПК'},
        'IiSiE2.xlsx': {'title': 'ИИСиЭ - расписание', 'description': 'Институт информационных систем и инженерии', 'institute': 'ИИСиЭ'},
        'IPBVM2.xls': {'title': 'ИПБиВМ - все курсы', 'description': 'Институт прикладной биотехнологии', 'institute': 'ИПБиВМ'},
        'IPP2.xls': {'title': 'ИПП - все курсы', 'description': 'Институт пищевых производств', 'institute': 'ИПП'},
        'IZKP2.xls': {'title': 'ИЗКиП - все курсы', 'description': 'Институт землеустройства, кадастров', 'institute': 'ИЗКиП'},
        'UI2.xlsx': {'title': 'Юридический институт', 'description': 'Юридический институт', 'institute': 'ЮИ'},
        'UIv2.xlsx': {'title': 'Юридический институт - вечернее отделение', 'description': 'Юридический институт, вечерняя форма', 'institute': 'ЮИ'},
    }

    # ==================== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ====================
    
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

    def read_excel_file(filename):
        filepath = os.path.join(RASP_FOLDER, filename)
        try:
            excel_file = pd.ExcelFile(filepath)
            html_parts = []
            groups = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                group_name = sheet_name
                
                # Определяем название группы
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
                
                # Селектор выбора группы
                html_parts.append('<div class="schedule-group-selector" data-unique="' + unique_id + '">')
                html_parts.append('<label>Выберите группу:</label>')
                html_parts.append('<select id="schedule-group-select-' + unique_id + '" class="schedule-group-select">')
                
                for i, group_name in enumerate(groups.keys()):
                    selected = 'selected' if i == 0 else ''
                    html_parts.append(f'<option value="{i}" {selected}>{group_name}</option>')
                html_parts.append('</select></div>')
                
                # Для каждой группы создаем контейнер с расписанием
                for i, (group_name, lessons) in enumerate(groups.items()):
                    display_style = "block" if i == 0 else "none"
                    
                    # Группировка по дням недели
                    lessons_by_day = {'mon': [], 'tue': [], 'wed': [], 'thu': [], 'fri': [], 'sat': [], 'sun': [], 'unknown': []}
                    for lesson in lessons:
                        day = lesson['day']
                        if day in lessons_by_day:
                            lessons_by_day[day].append(lesson)
                        else:
                            lessons_by_day['unknown'].append(lesson)
                    
                    html_parts.append(f'<div id="group-{unique_id}-{i}" class="schedule-group-container" style="display: {display_style};">')
                    html_parts.append(f'<h3 class="schedule-group-title">{group_name}</h3>')
                    
                    # Переключатели дней недели
                    html_parts.append('<div class="schedule-day-switcher-inner">')
                    day_buttons = [('all','Все дни'),('mon','ПН'),('tue','ВТ'),('wed','СР'),('thu','ЧТ'),('fri','ПТ'),('sat','СБ')]
                    for day_key, day_name in day_buttons:
                        active = 'active' if day_key == 'all' else ''
                        html_parts.append(f'<button class="day-btn-inner {active}" data-day="{day_key}">{day_name}</button>')
                    html_parts.append('</div>')
                    
                    # Вывод занятий по дням
                    day_names = {'mon':'Понедельник','tue':'Вторник','wed':'Среда','thu':'Четверг','fri':'Пятница','sat':'Суббота','unknown':'Другое'}
                    for day_key, day_name in day_names.items():
                        if lessons_by_day.get(day_key) and len(lessons_by_day[day_key]) > 0:
                            html_parts.append(f'<div class="schedule-day-section" data-day="{day_key}">')
                            html_parts.append(f'<h4 class="schedule-day-title">{day_name}</h4>')
                            html_parts.append('<div class="schedule-lessons-list">')
                            for lesson in lessons_by_day[day_key]:
                                lesson_type_class = f'lesson-type-{lesson["type"]}'
                                room_html = f'<span class="schedule-lesson-room">{lesson["room"]}</span>' if lesson['room'] else ''
                                html_parts.append('<div class="schedule-lesson-card ' + lesson_type_class + '">')
                                html_parts.append('<div class="schedule-lesson-time">' + lesson["time"] + '</div>')
                                html_parts.append('<div class="schedule-lesson-details">')
                                html_parts.append('<span class="schedule-lesson-subject">' + lesson["subject"] + '</span>')
                                html_parts.append('<span class="schedule-lesson-teacher">' + lesson["teacher"] + '</span>')
                                html_parts.append(room_html)
                                html_parts.append('</div></div>')
                            html_parts.append('</div></div>')
                    
                    html_parts.append('</div>')
                
                # JavaScript для переключения групп и дней
                html_parts.append('''
                <script>
                    document.querySelectorAll(".schedule-group-select").forEach(sel => {
                        sel.addEventListener("change", function() {
                            let id = this.id.replace("schedule-group-select-", "");
                            document.querySelectorAll(`[id^="group-${id}-"]`).forEach((c, i) => {
                                c.style.display = i == this.value ? "block" : "none";
                            });
                            let grp = document.querySelector(`#group-${id}-${this.value}`);
                            if (grp) {
                                grp.querySelectorAll(".day-btn-inner").forEach(b => b.classList.remove("active"));
                                let allBtn = grp.querySelector(".day-btn-inner[data-day='all']");
                                if (allBtn) allBtn.classList.add("active");
                                filterDaysInGroup(id, this.value, "all");
                            }
                        });
                    });
                    function filterDaysInGroup(uid, gidx, day) {
                        let grp = document.querySelector(`#group-${uid}-${gidx}`);
                        if (!grp) return;
                        grp.querySelectorAll(".schedule-day-section").forEach(s => {
                            s.style.display = (day === "all" || s.dataset.day === day) ? "block" : "none";
                        });
                    }
                    document.querySelectorAll(".day-btn-inner").forEach(btn => {
                        btn.addEventListener("click", function(e) {
                            e.preventDefault();
                            let parent = this.closest(".schedule-group-container");
                            let gidx = parent.id.split("-").pop();
                            let uid = parent.id.replace("group-", "").replace("-" + gidx, "");
                            document.querySelectorAll("#group-" + uid + "-" + gidx + " .day-btn-inner").forEach(b => b.classList.remove("active"));
                            this.classList.add("active");
                            filterDaysInGroup(uid, gidx, this.dataset.day);
                        });
                    });
                    document.querySelectorAll(".schedule-group-container").forEach((c, i) => {
                        if (i === 0) filterDaysInGroup(c.id.split("-")[1], 0, "all");
                    });
                </script>
                ''')
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
            html_parts.append('<div class="schedule-excel-sheet"><h3 class="schedule-sheet-title">' + sheet_name + '</h3><div class="schedule-readable-content">')
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
                    room_html = f'<span class="schedule-lesson-room">{cells[3]}</span>' if len(cells) > 3 else ''
                    html_parts.append('<div class="schedule-lesson-card" data-type="' + lesson_type + '">')
                    html_parts.append('<div class="schedule-lesson-time">' + cells[0] + '</div>')
                    html_parts.append('<div class="schedule-lesson-details">')
                    html_parts.append('<span class="schedule-lesson-subject">' + cells[1] + '</span>')
                    html_parts.append('<span class="schedule-lesson-teacher">' + cells[2] + '</span>')
                    html_parts.append(room_html)
                    html_parts.append('</div></div>')
                elif len(cells) == 2:
                    html_parts.append('<div class="schedule-info-row"><strong>' + cells[0] + ':</strong> ' + cells[1] + '</div>')
                else:
                    html_parts.append('<p class="schedule-text-line">' + cells[0] + '</p>')
            html_parts.append('</div></div>')
        return "".join(html_parts)
    except Exception as e:
        return f"<div class='schedule-error'>Ошибка чтения Excel: {str(e)}</div>"

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
        
        dynamic_templates = ['applicant_section', 'department', 'info_page', 'institute', 'science_section', 'student_section', 'university_section']
        
        if page.template in dynamic_templates:
            return render_template(f'dynamic/{page.template}.html', page=page, children=children)
        else:
            return render_template(f'{page.template}.html', page=page, children=children)

    @app.route('/institutes')
    def institutes_page():
        institutes = Page.query.filter_by(template='institute', published=True).all()
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

    # ==================== ВРЕМЕННЫЙ МАРШРУТ ДЛЯ СОЗДАНИЯ АДМИНА ====================
    @app.route('/create-admin-now')
    def create_admin_now():
        from models import db, User
        User.query.filter_by(username='admin').delete()
        admin = User(username='admin', email='admin@kgau.ru', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        return "✅ Админ создан! Логин: admin, Пароль: admin123"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)