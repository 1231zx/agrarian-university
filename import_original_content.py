import os
import re
from app import create_app
from models import db, Page

app = create_app()

# Путь к папке со старыми HTML файлами
OLD_PAGES_DIR = 'old_pages'  # укажите правильный путь

# Соответствие старых файлов и slug в БД
FILE_TO_SLUG = {
    # Университет и его страницы
    'university_main.html': 'university_main',
    'university_today.html': 'university_today',
    'university_history.html': 'university_history',
    'university_structure.html': 'structure',
    'university_leadership.html': 'leadership',
    'university_library.html': 'library',
    'university_popechitelskiy.html': 'university_popechitelskiy',
    'university_anticorruption.html': 'university_anticorruption',
    'university_parent_council.html': 'university_parent_council',
    'university_vesti_archive.html': 'university_vesti_archive',
    'university_press.html': 'university_press',
    'university_press_center.html': 'university_press_center',
    'university_brandbook.html': 'university_brandbook',
    'university_vesti.html': 'university_vesti',
    'university_media_about_us.html': 'university_media_about_us',
    'university_prosecutor.html': 'university_prosecutor',
    'university_quality_management.html': 'university_quality_management',
    'university_endowment.html': 'university_endowment',
    'university_driving_school.html': 'university_driving_school',
    'university_jalinga.html': 'university_jalinga',
    'university_association.html': 'university_association',
    'university_profsoyuz.html': 'university_profsoyuz',
    
    # Поступающему
    'applicant_main.html': 'applicant_main',
    'admission_info.html': 'admission_info',
    'admission_regulations.html': 'admission_regulations',
    'admission_docs.html': 'admission_docs',
    'admission_faq.html': 'admission_faq',
    'admission_addresses.html': 'admission_addresses',
    'admission_committee.html': 'admission_committee',
    'entrance_tests.html': 'entrance_tests',
    'exam_schedule.html': 'exam_schedule',
    'competition_lists.html': 'competition_lists',
    'applicant_lists.html': 'applicant_lists',
    'enrollment_info.html': 'enrollment_info',
    'target_education.html': 'target_education',
    'paid_education.html': 'paid_education',
    'bonuses.html': 'bonuses',
    'disabled_info.html': 'disabled_info',
    'dormitory.html': 'dormitory',
    'postgraduate_admission.html': 'postgraduate_admission',
    'doctoral_admission.html': 'doctoral_admission',
    
    # Студенту
    'student_main.html': 'student_main',
    'student_council.html': 'student_council',
    'student_teams.html': 'student_teams',
    'student_culture.html': 'student_culture',
    'student_sports.html': 'student_sports',
    'student_psychologist.html': 'student_psychologist',
    'student_social_support.html': 'student_social_support',
    'student_projects.html': 'student_projects',
    'student_faq.html': 'student_faq',
    'student_calendar.html': 'student_calendar',
    'student_scholarships.html': 'student_scholarships',
    'student_regulations.html': 'student_regulations',
    'student_educational_resources.html': 'student_educational_resources',
    'student_mass_courses.html': 'student_mass_courses',
    'student_textbooks.html': 'student_textbooks',
    'student_practice_bases.html': 'student_practice_bases',
    'student_practice_dates.html': 'student_practice_dates',
    'student_practice_docs.html': 'student_practice_docs',
    'student_practice_survey.html': 'student_practice_survey',
    'student_practice_instruction.html': 'student_practice_instruction',
    'student_practice_requests.html': 'student_practice_requests',
    'student_survey.html': 'student_survey',
    'international_students.html': 'international_students',
    
    # Наука
    'science_main.html': 'science_main',
    'science.html': 'science',
    'science_news.html': 'science_news',
    'science_schools.html': 'science_schools',
    'science_supervisors.html': 'science_supervisors',
    'laboratories.html': 'laboratories',
    'grants.html': 'grants',
    'conferences.html': 'conferences',
    'attestation.html': 'attestation',
    'candidate_exams.html': 'candidate_exams',
    'dissertations.html': 'dissertations',
    'postgraduate.html': 'postgraduate',
    'doctoral.html': 'doctoral',
    
    # Школьнику
    'school_info.html': 'school_info',
    'school_news.html': 'school_news',
    'school_conferences.html': 'school_conferences',
    'school_awards.html': 'school_awards',
    'olympiads.html': 'olympiads',
    'preparatory_courses.html': 'preparatory_courses',
    'agro_classes.html': 'agro_classes',
    'career_guidance.html': 'career_guidance',
    
    # Другие страницы
    'about.html': 'about',
    'contacts.html': 'contacts',
    'news.html': 'news',
    'programs.html': 'programs',
    'schedule.html': 'schedule',
    'volunteer.html': 'volunteer',
    'cossack.html': 'cossack',
    'payment.html': 'payment',
    'employee.html': 'employee',
    'employer.html': 'employer',
    'alumni.html': 'alumni',
    'contacts_departments.html': 'contacts_departments',
    'international.html': 'international',
    'university_life.html': 'university_life',
    'professionalitet.html': 'professionalitet',
    'inclusive_education.html': 'inclusive_education',
    'additional_education.html': 'additional_education',
    'educational_activity.html': 'educational_activity',
    
    # Институты
    'institute_agro.html': 'institute_agro',
    'institute_biotech.html': 'institute_biotech',
    'institute_economy.html': 'institute_economy',
    'institute_engineering.html': 'institute_engineering',
    'institute_food.html': 'institute_food',
    'institute_land.html': 'institute_land',
    'institute_law.html': 'institute_law',
    'institute_achinsk.html': 'institute_achinsk',
}

def extract_content_from_html(filepath):
    """Извлекает контент из HTML файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлекаем заголовок из <title>
        title_match = re.search(r'<title>(.*?)</title>', content)
        title = title_match.group(1).replace(' - ООО Аграрный Университет', '').replace(' - Красноярский ГАУ', '').strip() if title_match else None
        
        # Извлекаем контент из {% block content %}
        block_match = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL)
        body_content = block_match.group(1).strip() if block_match else content
        
        return title, body_content
    except Exception as e:
        print(f"❌ Ошибка чтения {filepath}: {e}")
        return None, None

def import_all_pages():
    with app.app_context():
        updated = 0
        created = 0
        not_found = []
        
        for filename, slug in FILE_TO_SLUG.items():
            filepath = os.path.join(OLD_PAGES_DIR, filename)
            
            if not os.path.exists(filepath):
                not_found.append(filename)
                continue
            
            title, content = extract_content_from_html(filepath)
            
            if not content:
                continue
            
            # Ищем страницу в БД
            page = Page.query.filter_by(slug=slug).first()
            
            if page:
                # Обновляем существующую
                if title:
                    page.title = title
                page.content = content
                page.published = True
                db.session.add(page)
                updated += 1
                print(f"✅ Обновлено: {slug} - {page.title}")
            else:
                # Создаём новую
                template = 'info_page'
                if 'applicant' in slug or 'admission' in slug:
                    template = 'applicant_section'
                elif 'student' in slug:
                    template = 'student_section'
                elif 'science' in slug:
                    template = 'science_section'
                elif 'institute' in slug:
                    template = 'institute'
                
                page = Page(
                    slug=slug,
                    title=title or slug.replace('_', ' ').title(),
                    content=content,
                    template=template,
                    published=True
                )
                db.session.add(page)
                created += 1
                print(f"✅ Создано: {slug} - {page.title}")
        
        db.session.commit()
        
        print(f"\n📊 ИТОГИ:")
        print(f"   Обновлено: {updated}")
        print(f"   Создано: {created}")
        print(f"   Не найдено файлов: {len(not_found)}")
        
        if not_found:
            print(f"\n⚠️ Файлы не найдены:")
            for f in not_found[:20]:
                print(f"   - {f}")

if __name__ == '__main__':
    import_all_pages()