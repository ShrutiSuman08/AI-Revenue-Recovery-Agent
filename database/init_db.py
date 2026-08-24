from .connection import engine, Base
from .models import Customer, Payment


def init_database():
    Base.metadata.create_all(bind=engine)
    print("Database created successfully!")


if __name__ == "__main__":
    init_database()