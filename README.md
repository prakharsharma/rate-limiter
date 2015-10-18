# Rate limiter

## Redis based generic rate limiter

A Redis based generic rate limiter that can be used for things like rate
limiting calls to an API

Provides
- simple to use API
- user can provided multiple rate limiting policies, for example number of API
  calls not to exceed
    - 20 calls per minute
    - 60 calls per 5 minutes
    - 1000 calls per 30 minutes
    - 100000 calls per hour

