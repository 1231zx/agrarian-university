from flask import jsonify, request
from models import db, Program, News, Contact

def init_api(app):
    
    # ==================== ПРОГРАММЫ API ====================
    @app.route('/api/v1/programs', methods=['GET'])
    def api_get_programs():
        programs = Program.query.order_by(Program.id).all()
        return jsonify({'programs': [p.to_dict() for p in programs]})
    
    @app.route('/api/v1/programs/<int:program_id>', methods=['GET'])
    def api_get_program(program_id):
        program = Program.query.get_or_404(program_id)
        return jsonify(program.to_dict())
    
    @app.route('/api/v1/programs', methods=['POST'])
    def api_create_program():
        data = request.json
        program = Program(
            name=data['name'],
            description=data['description'],
            duration=data['duration'],
            degree=data['degree']
        )
        db.session.add(program)
        db.session.commit()
        return jsonify({'message': 'Программа создана', 'id': program.id}), 201
    
    @app.route('/api/v1/programs/<int:program_id>', methods=['PUT'])
    def api_update_program(program_id):
        program = Program.query.get_or_404(program_id)
        data = request.json
        program.name = data.get('name', program.name)
        program.description = data.get('description', program.description)
        program.duration = data.get('duration', program.duration)
        program.degree = data.get('degree', program.degree)
        db.session.commit()
        return jsonify({'message': 'Программа обновлена'})
    
    @app.route('/api/v1/programs/<int:program_id>', methods=['DELETE'])
    def api_delete_program(program_id):
        program = Program.query.get_or_404(program_id)
        db.session.delete(program)
        db.session.commit()
        return jsonify({'message': 'Программа удалена'})
    
    # ==================== НОВОСТИ API ====================
    @app.route('/api/v1/news', methods=['GET'])
    def api_get_news():
        news = News.query.order_by(News.published_at.desc()).all()
        return jsonify({'news': [n.to_dict() for n in news]})
    
    @app.route('/api/v1/news/<int:news_id>', methods=['GET'])
    def api_get_news_item(news_id):
        news = News.query.get_or_404(news_id)
        return jsonify(news.to_dict())
    
    @app.route('/api/v1/news', methods=['POST'])
    def api_create_news():
        data = request.json
        news = News(
            title=data['title'],
            content=data['content'],
            author=data['author']
        )
        db.session.add(news)
        db.session.commit()
        return jsonify({'message': 'Новость создана', 'id': news.id}), 201
    
    @app.route('/api/v1/news/<int:news_id>', methods=['PUT'])
    def api_update_news(news_id):
        news = News.query.get_or_404(news_id)
        data = request.json
        news.title = data.get('title', news.title)
        news.content = data.get('content', news.content)
        news.author = data.get('author', news.author)
        db.session.commit()
        return jsonify({'message': 'Новость обновлена'})
    
    @app.route('/api/v1/news/<int:news_id>', methods=['DELETE'])
    def api_delete_news(news_id):
        news = News.query.get_or_404(news_id)
        db.session.delete(news)
        db.session.commit()
        return jsonify({'message': 'Новость удалена'})
    
    # ==================== КОНТАКТЫ API ====================
    @app.route('/api/v1/contacts', methods=['GET'])
    def api_get_contacts():
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return jsonify({'contacts': [c.to_dict() for c in contacts]})
    
    @app.route('/api/v1/contacts/<int:contact_id>', methods=['DELETE'])
    def api_delete_contact(contact_id):
        contact = Contact.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Сообщение удалено'})