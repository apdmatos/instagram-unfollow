from instagram_private_api import Client
from instagram_private_api_extensions import pagination
import time
from persistance import Persistence, Follower, Following

DAY_MILLIS = 24 * 60 * 60


class UnfollowBot:
    def __init__(self, username, password, unfollow_per_day=199, stop_on_failures=10):
        self._login(username, password)
        self.persistence = Persistence(username)
        self.sleep_time = DAY_MILLIS / unfollow_per_day
        self.failures = 0
        self.stop_on_failures = stop_on_failures

    def _login(self, username, password):
        print('authenticating {}... it may take a while'.format(username))
        self.api = Client(
            auto_patch=True, authenticate=True,
            username=username, password=password)

        print('successfully authenticated {}'.format(username))

    def _download_all_followers(self):
        if self.persistence.get_all_followers_downloaded():
            print('all followers have been downloaded... Skipping followers download')
            return

        print('downloading followers')

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
                print('error getting followeres from instagram')
                continue

            if results is None:
                break

            for follower in results['users']:
                entity = Follower(id=follower['id'], username=follower['username'])
                self.persistence.save_follower(entity)

        print('all followers have been downloaded. downloaded {} profiles'.format(count))
        self.persistence.all_followeres_downloaded()

    def _download_all_following(self):
        if self.persistence.get_all_following_downloaded():
            print('all following have been downloaded... Skipping following download')
            return

        print('downloading users I am following')

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
                print('error getting people I follow from instagram')
                continue

            if results is None:
                break

            for user in results['users']:
                entity = Following(id=user['id'], username=user['username'])
                self.persistence.save_follower(entity)

        print('all following have been downloaded. downloaded {} profiles'.format(count))
        self.persistence.all_following_downloaded()

    def _unfollow_batch(self, profiles_not_follow_back):
        for user in profiles_not_follow_back:
            print('trying to un follow user {}'.format(user.username))
            try:
                self.api.friendships_destroy(user.id)

                user.unfollowed = True
                self.persistence.save_following(user)

                print('successfuly un followed user {}'.format(user.username))
                print('sleeping for {} s'.format(self.sleep_time))
            except:
                self.failures += 1
                print('error trying to un follow user {}'.format(user.id))
                if self.failures > self.stop_on_failures:
                    return

            time.sleep(self.sleep_time)

    def start(self):

        self._download_all_following()
        self._download_all_followers()

        while True:

            if self.failures > self.stop_on_failures:
                print('stopping as we reached the max amount of failures...')
                break

            profiles_not_follow_back = self.persistence.get_not_following(100)
            if profiles_not_follow_back is None or len(profiles_not_follow_back) == 0:
                print('all profiles have been unfollowed!')
                break

            self._unfollow_batch(profiles_not_follow_back)

        print('Bye!')
