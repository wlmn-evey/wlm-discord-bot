from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, func, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from contextlib import contextmanager
import logging

from config import DATABASE_URL

# Set up logging
logger = logging.getLogger(__name__)

# Create database engine and session factory
engine = create_engine(DATABASE_URL, echo=False)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(SessionFactory)
Base = declarative_base()

# Context manager for database sessions
@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f'Database error: {e}')
        raise
    finally:
        session.close()

class BaseModel(Base):
    """Base model with common functionality."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(BaseModel):
    """User information and statistics."""
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    guild_id = Column(BigInteger, nullable=False, index=True)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    warnings = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    notes = Column(Text, default='')
    
    # Relationships
    warnings_list = relationship('Warning', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.user_id} in guild {self.guild_id}>'

class Activity(BaseModel):
    """User activity information."""
    __tablename__ = 'activity'
    
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    message_count = Column(Integer, default=0)

def get_or_create_activity(user_id):
    with Session() as session:
        activity = session.query(Activity).filter_by(user_id=user_id).first()
        if not activity:
            activity = Activity(user_id=user_id)
            session.add(activity)
            session.commit()
        return activity

def add_channel_warning(channel_id, moderator_id, guild_id, reason, warning_type):
    """Adds a warning associated with a channel rather than a user."""
    with session_scope() as session:
        warning = Warning(
            channel_id=channel_id,
            moderator_id=moderator_id,
            guild_id=guild_id,
            reason=reason,
            warning_type=warning_type,
            user_id=None # Explicitly null
        )
        session.add(warning)
        logger.info(f'Logged a {warning_type} flag for channel {channel_id}.')

def increment_message_count(user_id):
    with Session() as session:
        activity = get_or_create_activity(user_id)
        activity.message_count += 1
        session.commit()

class Warning(BaseModel):
    """Warning information for users."""
    __tablename__ = 'warnings'
    
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True) # Can be null for channel warnings
    guild_id = Column(BigInteger, nullable=False, index=True)
    moderator_id = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=False)
    warning_type = Column(String(20), default='yellow')  # 'yellow' or 'red'
    channel_id = Column(BigInteger, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', back_populates='warnings_list')
    
    def __repr__(self):
        return f'<{self.warning_type.capitalize()} warning for user {self.user_id} in guild {self.guild_id}>'

class GraduationQueue(BaseModel):
    """A queue of users to be graduated by the bot."""
    __tablename__ = 'graduation_queue'
    
    user_id = Column(BigInteger, primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow)

class TomatoStats(BaseModel):
    """Statistics for the tomato throwing game."""
    __tablename__ = 'tomato_stats'

    user_id = Column(BigInteger, primary_key=True)
    tomatoes_thrown = Column(Integer, default=0)
    tomatoes_landed = Column(Integer, default=0)
    tomatoes_dodged = Column(Integer, default=0)
    times_hit = Column(Integer, default=0)
    claimed_starter = Column(Boolean, default=False)
    coins = Column(Integer, default=0)
    last_daily_claim = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)

class TomatoInventory(BaseModel):
    """Inventory for the tomato throwing game."""
    __tablename__ = 'tomato_inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)


class GuildSettings(BaseModel):
    """Guild-specific settings."""
    __tablename__ = 'guild_settings'
    
    guild_id = Column(BigInteger, unique=True, nullable=False, index=True)
    mod_log_channel = Column(BigInteger, nullable=True)
    welcome_channel = Column(BigInteger, nullable=True)
    welcome_message = Column(Text, default='Welcome {user.mention} to {guild.name}!')
    mod_role = Column(BigInteger, nullable=True)
    admin_role = Column(BigInteger, nullable=True)
    
    def __repr__(self):
        return f'<GuildSettings for guild {self.guild_id}>'

def add_to_graduation_queue(user_id):
    """Adds a user to the graduation queue."""
    with session_scope() as session:
        # Check if already in queue
        existing = session.query(GraduationQueue).filter_by(user_id=user_id).first()
        if not existing:
            new_entry = GraduationQueue(user_id=user_id)
            session.add(new_entry)
            logger.info(f'User {user_id} added to graduation queue.')
            return True
        return False

def claim_starter_tomatoes(user_id):
    """Gives a user their starter tomatoes if they haven't claimed them yet."""
    with session_scope() as session:
        stats = get_or_create_tomato_stats(user_id)
        if not stats.claimed_starter:
            stats.claimed_starter = True
            add_to_inventory(user_id, 'Regular Tomato', 5)
            logger.info(f'User {user_id} claimed their starter tomatoes.')
            return True
        return False

def process_daily_claim(user_id):
    """Processes a daily claim for a user. Returns (success, message_or_coins)."""
    with session_scope() as session:
        stats = get_or_create_tomato_stats(user_id)
        now = datetime.utcnow()
        # Using 22 hours to give a bit of leeway
        if stats.last_daily_claim and (now - stats.last_daily_claim) < timedelta(hours=22):
            time_left = timedelta(hours=22) - (now - stats.last_daily_claim)
            # Format the timedelta to be more readable
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return (False, f"You can claim again in {hours}h {minutes}m.")

        # Grant reward
        daily_coins = random.randint(50, 150)
        stats.coins += daily_coins
        stats.last_daily_claim = now
        logger.info(f"User {user_id} claimed daily reward of {daily_coins} coins.")
        return (True, daily_coins)

def get_or_create_tomato_stats(user_id):
    """Gets or creates a user's tomato stats entry."""
    with session_scope() as session:
        stats = session.query(TomatoStats).filter_by(user_id=user_id).first()
        if not stats:
            stats = TomatoStats(user_id=user_id)
            session.add(stats)
            session.commit()
        return stats

def increment_tomato_stat(user_id, stat_name, value=1):
    """Increments a specific tomato stat for a user."""
    with session_scope() as session:
        stats = get_or_create_tomato_stats(user_id)
        if hasattr(stats, stat_name):
            setattr(stats, stat_name, getattr(stats, stat_name) + value)
            logger.info(f'Incremented {stat_name} for user {user_id} by {value}.')
        else:
            logger.error(f'Stat {stat_name} not found for user {user_id}.')

def get_leaderboard(stat_name, limit=10):
    """Gets the leaderboard for a specific stat."""
    with session_scope() as session:
        if not hasattr(TomatoStats, stat_name):
            return []
        return session.query(TomatoStats).order_by(getattr(TomatoStats, stat_name).desc()).limit(limit).all()

def get_inventory(user_id):
    """Gets a user's entire inventory."""
    with session_scope() as session:
        return session.query(TomatoInventory).filter_by(user_id=user_id).all()

def get_item_from_inventory(user_id, item_name):
    """Gets a specific item from a user's inventory."""
    with session_scope() as session:
        return session.query(TomatoInventory).filter_by(user_id=user_id, item_name=item_name).first()

def remove_from_inventory(user_id, item_name, quantity=1):
    """Removes an item from a user's inventory. Returns False if not enough items."""
    with session_scope() as session:
        item = session.query(TomatoInventory).filter_by(user_id=user_id, item_name=item_name).first()
        if item and item.quantity >= quantity:
            item.quantity -= quantity
            if item.quantity == 0:
                session.delete(item)
            logger.info(f'Removed {quantity} {item_name}(s) from inventory for user {user_id}.')
            return True
        return False

def add_to_inventory(user_id, item_name, quantity=1):
    """Adds an item to a user's inventory."""
    with session_scope() as session:
        item = session.query(TomatoInventory).filter_by(user_id=user_id, item_name=item_name).first()
        if item:
            item.quantity += quantity
        else:
            item = TomatoInventory(user_id=user_id, item_name=item_name, quantity=quantity)
            session.add(item)
        logger.info(f'Added {quantity} {item_name}(s) to inventory for user {user_id}.')

def get_and_clear_graduation_queue():
    """Gets all users from the queue and then clears it."""
    with session_scope() as session:
        pending_graduations = session.query(GraduationQueue).all()
        if not pending_graduations:
            return []
        
        user_ids = [entry.user_id for entry in pending_graduations]
        
        # Clear the queue
        session.query(GraduationQueue).delete()
        
        logger.info(f'Cleared {len(user_ids)} users from the graduation queue.')
        return user_ids

def init_database():
    """Initialize the database and create tables."""
    import os
    os.makedirs('data', exist_ok=True)
    Base.metadata.create_all(engine)
    logger.info('Database initialized')

# Initialize the database when this module is imported
init_db()
