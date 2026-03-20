from flask_restful import Api
from api.resources import (
    ProgramListResource, ProgramResource,
    NewsListResource, NewsResource,
    ContactListResource, ContactResource
)

def init_api(app):
    api = Api(app, prefix='/api/v1')
    
    # Маршруты для программ
    api.add_resource(ProgramListResource, '/programs')
    api.add_resource(ProgramResource, '/programs/<int:program_id>')
    
    # Маршруты для новостей
    api.add_resource(NewsListResource, '/news')
    api.add_resource(NewsResource, '/news/<int:news_id>')
    
    # Маршруты для контактов
    api.add_resource(ContactListResource, '/contacts')
    api.add_resource(ContactResource, '/contacts/<int:contact_id>')
    
    return api