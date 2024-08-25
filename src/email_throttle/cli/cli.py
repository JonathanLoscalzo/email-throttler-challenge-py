"""
Email Simulator CLI

This command-line interface (CLI) application is designed to simulate the process of sending emails through various
mail services.
It provides a flexible environment for configuring different strategies and scenarios to test the robustness and
reliability of your email systems locally.

Key features include:
- **Middleware support:** Implement retry mechanisms, rate limiters, and circuit breakers to simulate real-world 
conditions and stress-test your email services.
- **Customizable scenarios:** Adjust the number of emails, vendors, and middleware configurations to create diverse 
test cases.
- **Failover testing:** Optionally simulate failover states to ensure your email delivery system can handle vendor 
failures gracefully.

Commands and Arguments:

>>>
email-throttle-cli simulate
    --with-state-failover
            Enable stateful failover mechanism for vendors
    --email-count EMAIL_COUNT
            Number of emails to send
    --vendor-count VENDOR_COUNT
            Number of vendors/services
    --vendors VENDORS [VENDORS ...]
            Names of the vendors
    --middlewares MIDDLEWARES [MIDDLEWARES ...]
            Middlewares in the format retry,cb,rl per vendor
    --circuit-breakers CIRCUIT_BREAKERS [CIRCUIT_BREAKERS ...]
            Circuit breaker configuration in format threshold,reset_timeout
    --rate-limiters RATE_LIMITERS [RATE_LIMITERS ...]
            Rate limiter configuration in format max_attempts,per_seconds
    --retries RETRIES [RETRIES ...]
            Retry configuration in format retries
>>>

Usage examples:

# Simulate sending 30 emails through a single vendor using retry and rate limiter middlewares:
email-throttle-cli simulate \
    --email-count 30 --vendor-count 1 \
    --vendors vendor3 --middlewares retry,rl  \
    --retries 10 --rate-limiters 5,10

# Simulate sending 30 emails through three vendors with complex middleware configurations and failover:
email-throttle-cli simulate --email-count 30 --vendor-count 3 \
    --with-state-failover \
    --vendors vendor1 vendor2 vendor3 \
    --middlewares cb,rl rl,cb retry,rl  \
    --circuit-breakers 5,10 3,20 0 \
    --rate-limiters 10,5 5,10 3,5 \
    --retries 0 0 2
"""

import argparse
from datetime import timedelta

from loguru import logger

from email_throttle.cli.consumer import install_consumer_command
from email_throttle.cli.simulator import install_simulator_command


def main():
    logger.add("./logs/{time}.log", rotation=timedelta(minutes=1))
    parser = argparse.ArgumentParser(description="Email Simulator")

    subparsers = parser.add_subparsers()
    install_simulator_command(subparsers)
    install_consumer_command(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
