from flask import Flask
from application.database import db
from application.models  import User
app = None

def create_app():
    app = Flask(__name__)
    app.debug = True

    app.secret_key = 'mysecretkey'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'

    db.init_app(app)
    app.app_context().push()

    return app


app = create_app()

from application.controllers import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(type='admin').first()

        if not admin:
            default_admin = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                type='admin'
            )

            db.session.add(default_admin)
            db.session.commit()

    app.run(debug=True)
