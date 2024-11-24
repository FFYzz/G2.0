import asyncio
import random
import sys
import traceback

from imap_tools import MailboxLoginError

from core import Grass
from core.autoreger import AutoReger
from core.utils import logger, file_to_list
from core.utils.accounts_db import AccountsDB
from core.utils.exception import EmailApproveLinkNotFoundException, LoginException, RegistrationException
from data.config import THREADS, USER_ID_FILE_PATH


async def worker_task(_id, account: str, proxy: str = None, wallet: str = None, db: AccountsDB = None):
    user_id = account.split(";")[0]
    proxy = account.split(";")[1]
    grass = None
    try:
        grass = Grass(user_id=user_id, proxy=proxy, id=_id)
        await asyncio.sleep(random.uniform(1, 2) * _id)
        logger.info(f"Starting №{_id} | {user_id} | {proxy}")
        await grass.start()
        return True
    except (LoginException, RegistrationException) as e:
        logger.warning(f"{_id} | {e}")
    except MailboxLoginError as e:
        logger.error(f"{_id} | {e}")
    # except NoProxiesException as e:
    #     logger.warning(e)
    except EmailApproveLinkNotFoundException as e:
        logger.warning(e)
    except Exception as e:
        logger.error(f"{_id} | not handled exception | error: {e} {traceback.format_exc()}")
    finally:
        if grass:
            await grass.session.close()


async def main():
    user_id_with_proxy_list = file_to_list(USER_ID_FILE_PATH)

    if not user_id_with_proxy_list:
        logger.warning("No accounts found!")
        return

    autoreger = AutoReger.get_accounts(
        USER_ID_FILE_PATH,
        with_id=False,
        static_extra=None
    )

    threads = THREADS
    msg = "__MINING__ MODE"
    threads = len(autoreger.accounts)
    logger.info(msg)
    await autoreger.start(worker_task, threads)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    else:
        asyncio.run(main())
