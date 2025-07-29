from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()

naming_convention = {
    "ix": "ix_%(column_0_label)s",  # indexing -> for better querying
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # unique
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # ck -> CHECK -> validations CHECK age > 18;
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # foreign key
    "pk": "pk_%(table_name)s",  # primary key
}

metadata = MetaData(naming_convention=naming_convention)

# create a db instance
db = SQLAlchemy(metadata=metadata)

