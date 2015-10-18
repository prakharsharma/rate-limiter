#-*- coding: utf-8 -*-


def current_timestamp(seconds=False, milliseconds=False, microseconds=True):
    """
    Returns the current time as an int.
    The precision can be controlled to return the number of seconds,
    milliseconds, or microseconds.
    """
    now_ts = time.time()
    precision = 1000000
    if milliseconds:
        precision = 1000
    elif seconds:
        precision = 1
    return int(now_ts * precision)


class RateLimitExceededError(Exception):
    pass


def redis_zset_based_rate_limiter(redis_db, sorted_set_key, logger, seconds,
                                  limit, *args):
    """

    :param redis_db: handle to the redis DB where sorted set is stored
    :param sorted_set_key: key to the zset used for determining and
        limiting usage
    :param seconds: length of the time window in seconds
    :param limit: max number of allowed calls in :seconds
    :param args: additional seconds, limit as per the rate limiting policy
    :return:

    :raises RateLimitExceededError if rate limit is exceeded
    """

    def _enforcer(pipe):
        _enforcer.exceeded = False
        _enforcer.left_call_map = {}
        c_ts = current_timestamp()
        max_window = seconds
        policies = [(seconds, limit)]
        idx = 0
        while idx < len(args):
            if max_window <= args[idx]:
                max_window = args[idx]
            policies.append((args[idx], args[idx+1]))
            idx += 2

        for time_window_seconds, _limit in policies:
            range_results = pipe.zrangebyscore(
                sorted_set_key,
                c_ts - time_window_seconds*1000000,
                c_ts,
                withscores=True
            )
            num_calls = 0
            for member, score in range_results:
                parts = member.split(':')
                num_calls += int(parts[1])
            # add the current call
            num_calls += 1
            if num_calls > _limit:
                _enforcer.exceeded = True
            else:
                _enforcer.left_call_map[time_window_seconds] =\
                    _limit - num_calls

        results = pipe.zrangebyscore(
            sorted_set_key, c_ts, c_ts, withscores=True
        )
        if len(results) > 0:
            c_member, c_score = results[0]
            parts = c_member.split(':')
            c_member = '%s:%s' % (c_ts, int(parts[1]) + 1)
        else:
            c_member = '%s:1' % c_ts
            c_score = c_ts

        pipe.multi()
        pipe.zadd(sorted_set_key, c_score, c_member)
        pipe.zremrangebyscore(
            sorted_set_key,
            0,
            (c_ts - max_window*1000000) - 1
        )

    _enforcer.exceeded = False
    _enforcer.left_call_map = {}
    redis_db.transaction(_enforcer, sorted_set_key)
    if logger:
        logger.debug('rate limiter result: exceeded: %s, left_call_map: %s' % (
            _enforcer.exceeded, _enforcer.left_call_map))
    if _enforcer.exceeded:
        raise RateLimitExceededError()
    return _enforcer.left_call_map

