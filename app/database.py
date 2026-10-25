
from sqlalchemy import create_engine


DATABASE_URL = "postgresql+psycopg:///proofstack"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
