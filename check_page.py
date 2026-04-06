from app import create_app
from models import db, Page

app = create_app()
with app.app_context():
    p = Page.query.filter_by(slug='contacts_departments').first()
    if p:
        print(f'id={p.id}, title={p.title}, published={p.published}, template={p.template}')
    else:
        print('Not found')