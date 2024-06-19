import json
import logging

from yadisk import YaDisk
from yadisk.exceptions import YaDiskError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class YaDiskClient:
    def __init__(self, token):
        self.token = token
        self.disk = YaDisk(token=token)

    async def check_token_validity(self):
        disk = YaDisk(token=self.token)
        try:
            if disk.check_token():
                logger.info("Token is valid")
                return True
            else:
                logger.warning("Token is invalid")
                return False
        except YaDiskError as e:
            logger.error(f"Error checking token: {e}")
            return False

    async def get_json_of_items_dates_from_yandex_disk(self, directory_path):
        y = YaDisk(token=self.token)

        if not await self.check_token_validity():
            return None

        try:
            items = y.listdir(f"disk:/{directory_path}")
            logger.info(f"Contents of the directory {directory_path} retrieved")
        except Exception as e:
            logger.error(f"Error retrieving directory contents: {e}")
            return None

        if not items:
            logger.warning("The directory is empty or does not exist.")
            return None

        modified_times = {f"item_{i}": item.modified.isoformat() for i, item in enumerate(items)}

        return json.dumps(modified_times, ensure_ascii=False)
