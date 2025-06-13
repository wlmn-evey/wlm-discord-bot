import gspread
from google.oauth2.service_account import Credentials
import logging
import os

from config import GSHEET_SPREADSHEET_NAME, GSHEET_WORKSHEET_NAME

logger = logging.getLogger(__name__)

# Define the scope for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'data/gcp_service_account.json'

class GSheetClient:
    """A client for interacting with Google Sheets."""

    def __init__(self):
        self.creds = None
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    def connect(self):
        """Establish a connection to the Google Sheets API."""
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f'Service account file not found at {SERVICE_ACCOUNT_FILE}')
            logger.error('Please follow the setup instructions to create it.')
            return False

        try:
            self.creds = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            self.client = gspread.authorize(self.creds)
            logger.info('Successfully connected to Google Sheets API')
            return True
        except Exception as e:
            logger.error(f'Failed to connect to Google Sheets: {e}')
            return False

    def get_or_create_spreadsheet(self):
        """Get the spreadsheet or create it if it doesn't exist."""
        if not self.client:
            return False

        try:
            self.spreadsheet = self.client.open(GSHEET_SPREADSHEET_NAME)
            logger.info(f'Opened spreadsheet: {GSHEET_SPREADSHEET_NAME}')
        except gspread.exceptions.SpreadsheetNotFound:
            logger.info(f'Spreadsheet not found, creating it...')
            self.spreadsheet = self.client.create(GSHEET_SPREADSHEET_NAME)
            # Share with users if needed (e.g., your own email)
            # self.spreadsheet.share('your-email@example.com', perm_type='user', role='writer')

        try:
            self.worksheet = self.spreadsheet.worksheet(GSHEET_WORKSHEET_NAME)
            logger.info(f'Opened worksheet: {GSHEET_WORKSHEET_NAME}')
        except gspread.exceptions.WorksheetNotFound:
            logger.info(f'Worksheet not found, creating it...')
            self.worksheet = self.spreadsheet.add_worksheet(
                title=GSHEET_WORKSHEET_NAME, rows=100, cols=20
            )
            self._setup_header()

        return True

    def _setup_header(self):
        """Set up the header row in the worksheet."""
        if not self.worksheet:
            return

        header = [
            'Channel ID', 'Channel Name', 'Category',
            'Has Topic', 'Has Pinned Messages', 'Naming Convention OK',
            'Permissions OK', 'Last Message Timestamp', 'Message Count (14d)',
            'Is Under-utilized', 'Moderation Actions',
            'Health Score', 'Last Updated'
        ]
        self.worksheet.update('A1', [header])
        self.worksheet.format('A1:M1', {'textFormat': {'bold': True}})
        logger.info('Worksheet header has been set up')

    def update_channel_data(self, channel_id, data):
        """Update a row of data for a specific channel."""
        if not self.worksheet:
            return

        try:
            cell = self.worksheet.find(str(channel_id))
            row_index = cell.row
            self.worksheet.update(f'A{row_index}', [list(data.values())])
            logger.info(f'Updated data for channel {channel_id}')
        except gspread.exceptions.CellNotFound:
            # If channel not found, append a new row
            self.worksheet.append_row(list(data.values()))
            logger.info(f'Appended new data for channel {channel_id}')

# Singleton instance of the client
gsheet_client = GSheetClient()

def init_gsheet_client():
    """Initialize the Google Sheets client."""
    if gsheet_client.connect():
        gsheet_client.get_or_create_spreadsheet()
