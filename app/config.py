"""Environment-based configuration shared by web and management entry points."""
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get('GABAY_DATABASE_PATH', BASE_DIR / 'database' / 'als_gabay.db')).expanduser().resolve()
REFERENCE_DIR = BASE_DIR / 'data' / 'reference'
ONET_SOURCE_DIR = BASE_DIR / 'data' / 'source' / 'onet'
RIASEC_COLUMNS = ('realistic', 'investigative', 'artistic', 'social', 'enterprising', 'conventional')
