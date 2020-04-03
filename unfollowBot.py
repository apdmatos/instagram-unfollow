from instagram_web_api import Client, ClientThrottledError, ClientBadRequestError, ClientForbiddenError
from instagram_private_api_extensions import pagination
import time
from persistance import Persistence, Follower, Following
import hashlib
import string
import random
import logging

DAY_MILLIS = 24 * 60 * 60
logger = logging.getLogger(__name__)


###########################################
# hack to fir an issue in the web api
class MyClient(Client):
    @staticmethod
    def _extract_rhx_gis(html):
        options = string.ascii_lowercase + string.digits
        text = ''.join([random.choice(options) for _ in range(8)])
        return hashlib.md5(text.encode()).hexdigest()


class UnfollowBot:
    def __init__(self, username, password, unfollow_per_day=199, stop_on_failures=10):
        self._username = username
        self._password = password
        self._login()
        self.persistence = Persistence(username)
        self.sleep_time = DAY_MILLIS / unfollow_per_day
        self.failures = 0
        self.stop_on_failures = stop_on_failures

    def _login(self):
        logger.info('authenticating {}... it may take a while'.format(self._username))
        self.api = MyClient(
            auto_patch=True, authenticate=True,
            username=self._username, password=self._password)

        logger.info('successfully authenticated {}'.format(self._username))

    def _download_all_followers(self):
        if self.persistence.get_all_followers_downloaded():
            logger.info('all followers have been downloaded... Skipping followers download')
            return

        logger.info('downloading followers')

        count = 0
        rank_token = self.api.generate_uuid()
        followers = pagination.page(self.api.user_followers,
                                    args={'user_id': self.api.authenticated_user_id, 'rank_token': rank_token}, wait=10)
        it = iter(followers)

        while True:
            if self.failures > self.stop_on_failures:
                return
            try:
                results = next(it, None)
                count += len(results['users'])
            except:
                self.failures += 1
                logger.error('error getting followeres from instagram')
                continue

            if results is None:
                break

            for follower in results['users']:
                entity = Follower(id=follower['id'], username=follower['username'])
                self.persistence.save_follower(entity)

        logger.info('all followers have been downloaded. downloaded {} profiles'.format(count))
        self.persistence.all_followeres_downloaded()

    def _download_all_following(self):
        if self.persistence.get_all_following_downloaded():
            logger.info('all following have been downloaded... Skipping following download')
            return

        logger.info('downloading users I am following')

        rank_token = self.api.generate_uuid()
        following = pagination.page(self.api.user_following,
                                    args={'user_id': self.api.authenticated_user_id, 'rank_token': rank_token}, wait=10)

        count = 0
        it = iter(following)
        while True:
            if self.failures > self.stop_on_failures:
                return
            try:
                results = next(it, None)
                count += len(results['users'])
            except:
                self.failures += 1
                logger.error('error getting people I follow from instagram')
                continue

            if results is None:
                break

            for user in results['users']:
                entity = Following(id=user['id'], username=user['username'])
                self.persistence.save_follower(entity)

        logger.info('all following have been downloaded. downloaded {} profiles'.format(count))
        self.persistence.all_following_downloaded()

    def _unfollow_batch(self, profiles_not_follow_back):
        for user in profiles_not_follow_back:
            logger.info('trying to un follow user {}'.format(user.username))
            try:
                self.api.friendships_destroy(user.id)

                user.unfollowed = True
                self.persistence.save_following(user)

                logger.info('successfuly un followed user {}'.format(user.username))

            except ClientBadRequestError:
                logger.info("user {} does not exist anymore".format(user.username))
                user.unfollowed = True
                self.persistence.save_following(user)

            except ClientThrottledError:
                self.failures += 1
                logger.error('throttle error trying to un follow user {}'.format(user.id))
                if self.failures > self.stop_on_failures:
                    return

            except ClientForbiddenError:
                logger.error("session has expired... We need to authenticate again")
                self._login()

            except Exception as e:
                logger.error("error happened while trying to unfollow user {}".format(user.username), e)

            logger.info('sleeping for {}s'.format(self.sleep_time))
            time.sleep(self.sleep_time)

    def start(self):

        self._download_all_following()
        self._download_all_followers()

        while True:

            if self.failures > self.stop_on_failures:
                logger.info('stopping as we reached the max amount of failures...')
                break

            profiles_not_follow_back = self.persistence.get_not_following(100)
            if profiles_not_follow_back is None or len(profiles_not_follow_back) == 0:
                logger.info('all profiles have been unfollowed!')
                break

            self._unfollow_batch(profiles_not_follow_back)

        logger.info('Bye!')
