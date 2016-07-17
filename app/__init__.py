from flask import Flask, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config.from_object('config')
db = SQLAlchemy(app)
    
# Import Blueprint modules.
from app.missions.routes import mod_missions

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error=error), 404

# Register Blueprint(s)
app.register_blueprint(mod_missions)

db.create_all(bind=['missionary'])