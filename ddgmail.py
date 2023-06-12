#!/usr/bin/env python3

import json
import os
import sys

import click
import requests

BASE_URL = "https://quack.duckduckgo.com/api/"
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
#    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://duckduckgo.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-GPC": "1",
}
session = requests.Session()
session.headers.update(BASE_HEADERS)

APP_NAME = "ddgmail-py"
config_dir = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), APP_NAME
)
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, "config.json")


def load_config():
    config = None

    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)

    if (
        not config
        or not config.get("user")
        or not config.get("token")
        or not config.get("access_token")
    ):
        raise click.ClickException("Login first")

    return config


def save_config(config):
    with open(config_file, "w") as f:
        json.dump(config, f)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("username")
def request_otp(username):
    """Request OTP code to login"""
    response = session.get(BASE_URL + "auth/loginlink", params={"user": username})
    response.raise_for_status()
    click.echo("Please check your inbox for the magic password!")


@cli.command()
@click.argument("username")
def login(username, otp=None):
    """Login to the account with OTP"""
    while not otp:
        otp = click.prompt("Enter the magic password", type=str)

    config = {}
    response = session.get(
        BASE_URL + "auth/login", params={"user": username, "otp": otp}
    )
    response.raise_for_status()
    data = response.json()
    if data["status"] != "authenticated":
        raise click.ClickException("Login failed")
    config["user"] = username
    config["token"] = data["token"]
    response = session.get(
        BASE_URL + "email/dashboard",
        headers={"Authorization": f"Bearer {data['token']}"},
    )
    response.raise_for_status()
    data = response.json()
    config["access_token"] = data["user"]["access_token"]
    # write to config
    save_config(config)
    click.echo("Login successful")


@cli.command()
def dashboard():
    """Show dashboard information"""
    config = load_config()
    response = session.get(
        BASE_URL + "email/dashboard",
        headers={"Authorization": f"Bearer {config['token']}"},
    )
    response.raise_for_status()
    data = response.json()
    mapping = {
        "stats": {
            "addresses_generated": "Addresses Generated",
        },
        "user": {
            "email": "Forwarding Email",
        },
    }
    for section, section_data in data.items():
        if section in mapping:
            for key, value in section_data.items():
                if key in mapping[section]:
                    click.echo(f"{mapping[section][key]}: {value}")


@cli.command()
@click.argument("email")
def change_forwarding_email(email):
    """Change forwarding email"""
    config = load_config()
    data = {"email": email, "disable_secure_reply": 0}
    response = session.post(
        BASE_URL + "email/change-email-address",
        headers={"Authorization": f"Bearer {config['token']}"},
        data=data,
    )
    response.raise_for_status()
    click.echo("Forwarding email changed")


@cli.command()
def generate_new_alias():
    """Generates a new E-Mail alias"""
    config = load_config()
    response = session.post(
        BASE_URL + "email/addresses",
        headers={"Authorization": f"Bearer {config['access_token']}"},
    )
    response.raise_for_status()
    data = response.json()
    if sys.stdout.isatty():
        click.echo(f"Generated E-Mail Address: {data['address']}@duck.com")
    else:
        click.echo(f"{data['address']}@duck.com")


if __name__ == "__main__":
    cli()
