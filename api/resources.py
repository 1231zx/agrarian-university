from flask_restful import Resource, reqparse
from flask import jsonify

# Парсеры для валидации данных
program_parser = reqparse.RequestParser()
program_parser.add_argument('name', type=str, required=True, help='Название программы обязательно')
program_parser.add_argument('description', type=str, required=True, help='Описание обязательно')
program_parser.add_argument('duration', type=str, required=True, help='Длительность обязательна')
program_parser.add_argument('degree', type=str, required=True, help='Степень обязательна')

news_parser = reqparse.RequestParser()
news_parser.add_argument('title', type=str, required=True, help='Заголовок обязателен')
news_parser.add_argument('content', type=str, required=True, help='Содержание обязательно')
news_parser.add_argument('author', type=str, required=True, help='Автор обязателен')

contact_parser = reqparse.RequestParser()
contact_parser.add_argument('name', type=str, required=True, help='Имя обязательно')
contact_parser.add_argument('email', type=str, required=True, help='Email обязателен')
contact_parser.add_argument('phone', type=str, required=True, help='Телефон обязателен')
contact_parser.add_argument('message', type=str, required=True, help='Сообщение обязательно')

# API Resources для программ
class ProgramListResource(Resource):
    def get(self):
        from models import Program
        programs = Program.query.all()
        return {'programs': [p.to_dict() for p in programs]}, 200
    
    def post(self):
        from models import Program, db
        args = program_parser.parse_args()
        program = Program(
            name=args['name'],
            description=args['description'],
            duration=args['duration'],
            degree=args['degree']
        )
        db.session.add(program)
        db.session.commit()
        return {'message': 'Программа создана', 'program': program.to_dict()}, 201

class ProgramResource(Resource):
    def get(self, program_id):
        from models import Program
        program = Program.query.get_or_404(program_id)
        return program.to_dict(), 200
    
    def put(self, program_id):
        from models import Program, db
        program = Program.query.get_or_404(program_id)
        args = program_parser.parse_args()
        
        program.name = args['name']
        program.description = args['description']
        program.duration = args['duration']
        program.degree = args['degree']
        
        db.session.commit()
        return {'message': 'Программа обновлена', 'program': program.to_dict()}, 200
    
    def delete(self, program_id):
        from models import Program, db
        program = Program.query.get_or_404(program_id)
        db.session.delete(program)
        db.session.commit()
        return {'message': 'Программа удалена'}, 200

# API Resources для новостей
class NewsListResource(Resource):
    def get(self):
        from models import News
        news = News.query.order_by(News.published_at.desc()).all()
        return {'news': [n.to_dict() for n in news]}, 200
    
    def post(self):
        from models import News, db
        args = news_parser.parse_args()
        news_item = News(
            title=args['title'],
            content=args['content'],
            author=args['author']
        )
        db.session.add(news_item)
        db.session.commit()
        return {'message': 'Новость создана', 'news': news_item.to_dict()}, 201

class NewsResource(Resource):
    def get(self, news_id):
        from models import News
        news_item = News.query.get_or_404(news_id)
        return news_item.to_dict(), 200
    
    def put(self, news_id):
        from models import News, db
        news_item = News.query.get_or_404(news_id)
        args = news_parser.parse_args()
        
        news_item.title = args['title']
        news_item.content = args['content']
        news_item.author = args['author']
        
        db.session.commit()
        return {'message': 'Новость обновлена', 'news': news_item.to_dict()}, 200
    
    def delete(self, news_id):
        from models import News, db
        news_item = News.query.get_or_404(news_id)
        db.session.delete(news_item)
        db.session.commit()
        return {'message': 'Новость удалена'}, 200

# API Resources для контактов
class ContactListResource(Resource):
    def get(self):
        from models import Contact
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return {'contacts': [c.to_dict() for c in contacts]}, 200
    
    def post(self):
        from models import Contact, db
        args = contact_parser.parse_args()
        contact = Contact(
            name=args['name'],
            email=args['email'],
            phone=args['phone'],
            message=args['message']
        )
        db.session.add(contact)
        db.session.commit()
        return {'message': 'Сообщение отправлено', 'contact': contact.to_dict()}, 201

class ContactResource(Resource):
    def get(self, contact_id):
        from models import Contact
        contact = Contact.query.get_or_404(contact_id)
        return contact.to_dict(), 200
    
    def delete(self, contact_id):
        from models import Contact, db
        contact = Contact.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        return {'message': 'Сообщение удалено'}, 200