from unfollowBot import UnfollowBot
import logging

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='unfollow instagram users which do not follow me back.')
    parser.add_argument('username', metavar='username', nargs=1,
                        help='instagram username')
    parser.add_argument('password', metavar='username', nargs=1,
                        help='instagram password')
    parser.add_argument('--unfollow-per-day', metavar='unfollow_per_day', default=199,
                        help='number of users to unfollow per day')
    parser.add_argument('--stop-on-failures', metavar='stop_on_failures', default=10,
                        help='To avoid being blocked stops the bot when it gets n number of failures')
    parser.add_argument('-debug', '--debug', help="output more detailed information about the bot", action='store_true')
    args = parser.parse_args()

    username = args.username[0]
    password = args.password[0]

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    bot = UnfollowBot(username, password, args.unfollow_per_day, args.stop_on_failures)
    bot.start()
