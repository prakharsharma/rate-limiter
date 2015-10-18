#-*- coding: utf-8 -*-

import redis
import unittest
import time

from rate_limiter import redis_zset_based_rate_limiter, \
    RateLimitExceededError


class RateLimiterTest(unittest.TestCase):

    def setUp(self):
        self.db = redis.StrictRedis()
        self.rate_limit_key = 'zs:rate_limit_test'

    def tearDown(self):
        self.db.delete(self.rate_limit_key)
        pass

    def test_rate_limiter1(self):
        for _ in range(0, 5):
            try:
                redis_zset_based_rate_limiter(
                    self.db, self.rate_limit_key, 5, 6
                )
            except RateLimitExceededError:
                self.assertTrue(False)
        try:
            redis_zset_based_rate_limiter(
                self.db, self.rate_limit_key, 5, 6
            )
        except RateLimitExceededError:
            self.assertTrue(True)

        time.sleep(5)
        try:
            redis_zset_based_rate_limiter(
                self.db, self.rate_limit_key, 5, 6
            )
        except RateLimitExceededError:
            self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()

