from flask_sqlalchemy import SQLAlchemy

# db lives here so app.py and models.py can both import it
# without creating a circular dependency between each other
db = SQLAlchemy()
