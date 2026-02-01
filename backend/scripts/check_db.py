import sys
import os
import logging

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import check_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Testing database connection...")
    if check_db_connection():
        logger.info("✅ Database connection successful!")
        sys.exit(0)
    else:
        logger.error("❌ Database connection failed.")
        sys.exit(1)