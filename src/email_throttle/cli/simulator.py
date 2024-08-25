import argparse

from loguru import logger

from email_throttle.core.entity import EmailMessage
from email_throttle.core.failover import EmailFailover, EmailFailoverWithState
from email_throttle.core.middlewares.default.circuit_breaker import \
    CircuitBreaker
from email_throttle.core.middlewares.default.rate_limiter import RateLimiter
from email_throttle.core.middlewares.default.retry import Retry
from email_throttle.core.service import EmailService
from email_throttle.vendors.noop import NoOpEmailSender


def install_simulator_command(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
):
    subparser = subparsers.add_parser("simulate", help="Simulate sending emails")
    subparser.add_argument(
        "--with-state-failover",
        default=False,
        action="store_true",
        help="Enable stateful failover mechanism for vendors (EmailFailoverWithState or EmailFailover)",
    )
    subparser.add_argument(
        "--email-count",
        type=int,
        required=True,
        help="Number of emails to send. e.g.: 100",
    )
    subparser.add_argument(
        "--vendor-count",
        type=int,
        required=True,
        help="Number of vendors/service: 3",
    )
    subparser.add_argument(
        "--vendors",
        nargs="+",
        required=True,
        help="Names of the vendors. e.g.: sns sendgrid gridsend",
    )
    subparser.add_argument(
        "--middlewares",
        nargs="+",
        required=True,
        help="Middlewares in the format retry,cb,rl per vendor. e.g.: retry,cb cb,lr retry retry,cb,lr ",
    )
    subparser.add_argument(
        "--circuit-breakers",
        nargs="+",
        required=False,
        default="",
        help="Circuit breaker configuration in format threshold,reset_timeout. e.g.: 2,10 3,20",
    )
    subparser.add_argument(
        "--rate-limiters",
        nargs="+",
        required=False,
        default="",
        help="Rate limiter configuration in format max_attempts,per_seconds. e.g.: 2,10 3,20",
    )
    subparser.add_argument(
        "--retries",
        nargs="+",
        required=False,
        default="",
        help="Retry configuration in format retries. e.g.: 10",
    )
    subparser.set_defaults(func=command_simulate)
    return subparser


def parse_args(args):
    vendors_config = []

    for i in range(args.vendor_count):
        vendor_config = {
            "name": args.vendors[i],
            "middlewares": args.middlewares[i].split(","),  # cb,rl,retry
        }

        for middleware in vendor_config["middlewares"]:
            if middleware == "cb" and "circuit_breaker" not in vendor_config:
                cb_threshold, cb_reset_timeout = map(
                    int,
                    args.circuit_breakers[i].split(","),
                )
                vendor_config = {
                    **vendor_config,
                    "circuit_breaker": {
                        "threshold": cb_threshold,
                        "reset_timeout": cb_reset_timeout,
                    },
                }
            elif middleware == "rl" and "rate_limiter" not in vendor_config:
                rl_max_attempts, rl_per_seconds = map(
                    int,
                    args.rate_limiters[i].split(","),
                )
                vendor_config = {
                    **vendor_config,
                    "rate_limiter": {
                        "max_attempts": rl_max_attempts,
                        "per_seconds": rl_per_seconds,
                    },
                }
            elif middleware == "retry" and "retry" not in vendor_config:
                retries = int(args.retries[i])
                vendor_config = {
                    **vendor_config,
                    "retry": {
                        "retries": retries,
                    },
                }

        vendors_config.append(vendor_config)
    return vendors_config


def create_services(vendors_config: list[dict]) -> list[EmailService]:
    services = []
    for config in vendors_config:
        vendor = NoOpEmailSender(config["name"])
        middlewares = []
        for middleware in config.get("middlewares", []):
            if middleware == "rl":
                m = RateLimiter(
                    config["rate_limiter"]["max_attempts"],
                    config["rate_limiter"]["per_seconds"],
                )
            if middleware == "cb":
                m = CircuitBreaker(
                    config["circuit_breaker"]["threshold"],
                    config["circuit_breaker"]["reset_timeout"],
                )
            elif middleware == "retry":
                m = Retry(
                    config["retry"]["retries"],
                )
            middlewares.append(m)
        service = EmailService(vendor, middlewares)
        services.append(service)
    return services


def generate_emails(num_emails):
    for i in range(num_emails):
        yield EmailMessage(
            subject=f"Test Email {i}",
            body=f"This is a test email {i}",
            to="email",
            from_email="from",
        )


def send_emails(services, email_count, with_state_failover):
    if with_state_failover:
        failover = EmailFailoverWithState(services)  # or EmailFailover
    else:
        failover = EmailFailover(services)
    errors = []

    for message in generate_emails(num_emails=email_count):
        if not failover.send_email(message):
            errors.append(message)

    return errors


def command_simulate(args):
    if len(args.vendors) != args.vendor_count or len(args.middlewares) != args.vendor_count:
        raise ValueError("Number of vendors must match number of vendors_count")

    vendors_config = parse_args(args)
    services = create_services(vendors_config)
    errors = send_emails(services, args.email_count, args.with_state_failover)

    logger.info(f"Emails {args.email_count}")
    logger.info(f"Errors {len(errors)}")
