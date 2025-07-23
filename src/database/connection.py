import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from src.database.models import Base
from src.utils.logger import logger
from contextlib import contextmanager


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        try:
            # Get database configuration from environment
            db_host = os.getenv('POSTGRES_HOST', 'localhost')
            db_port = os.getenv('POSTGRES_PORT', '5432')
            db_user = os.getenv('POSTGRES_USER', 'raguser')
            db_password = os.getenv('POSTGRES_PASSWORD', 'ragpassword')
            db_name = os.getenv('POSTGRES_DB', 'ragchatbot')
            
            # Construct database URL
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=10,
                max_overflow=20,
                echo=False  # Set to True for SQL query logging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    # def drop_tables(self):
    #     """Drop all tables from the database"""
    #     try:
    #         Base.metadata.drop_all(bind=self.engine)
    #         logger.info("Database tables dropped successfully")
    #     except Exception as e:
    #         logger.error(f"Failed to drop database tables: {e}")
    #         raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()