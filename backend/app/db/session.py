from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
import os
from sqlalchemy.engine import URL



url = URL.create(
    drivername="mysql+pymysql",
    username=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DB,
)

# Initiate the connection
engine = create_engine(url, echo=False)

# Create the instance we are looking for
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)