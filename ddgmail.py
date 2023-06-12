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
    # "Accept-Encoding": "gzip, deflate, br",
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
        with open(config_file, encoding="utf-8") as fobj:
            config = json.load(fobj)

    if (
        not config
        or not config.get("user")
        or not config.get("token")
        or not config.get("access_token")
    ):
        raise click.ClickException("Login first")

    return config


def save_config(config):
    with open(config_file, "w", encoding="utf-8") as fobj:
        json.dump(config, fobj)


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
@click.pass_context
def login(ctx: click.Context, username, otp=None, tries=0):
    """Login to the account with OTP"""
    while not otp:
        otp = click.prompt("Enter the magic password", type=str)

    config = {}
    response = session.get(
        BASE_URL + "auth/login", params={"user": username, "otp": otp}
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code != 401:
            raise ex
        if tries >= 3:
            raise click.ClickException("Retry threshold exceeded")
        click.echo("Invalid magic password", err=True)
        ctx.invoke(login, username=username, otp=None, tries=tries + 1)
        return
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


def row_string_fmt(str1: str, str2: str, size: int):
    return f"{str1:>{size}} | {str2}"


@cli.command()
@click.pass_context
def dashboard(ctx: click.Context, tries=0):
    """Show dashboard information"""
    config = load_config()
    response = session.get(
        BASE_URL + "email/dashboard",
        headers={"Authorization": f"Bearer {config['token']}"},
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code != 401:
            raise ex
        if tries >= 3:
            raise click.ClickException("Retry threshold exceeded")
        ctx.invoke(request_otp, username=config["user"])
        ctx.invoke(login, username=config["user"], otp=None)
        ctx.invoke(dashboard, tries=tries + 1)
        return
    data = response.json()
    click.echo(row_string_fmt("Duck Address", f"{config['user']}@duck.com", 20))
    click.echo(row_string_fmt("Forwarding Address", data["user"]["email"], 20))
    click.echo(
        row_string_fmt("Addresses Generated", data["stats"]["addresses_generated"], 20)
    )


@cli.command()
@click.argument("email")
@click.pass_context
def change_forwarding_email(ctx: click.Context, email, tries=0):
    """Change forwarding email"""
    config = load_config()
    data = {"email": email, "disable_secure_reply": 0}
    response = session.post(
        BASE_URL + "email/change-email-address",
        headers={"Authorization": f"Bearer {config['token']}"},
        data=data,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code != 401:
            raise ex
        if tries >= 3:
            raise click.ClickException("Retry threshold exceeded")
        ctx.invoke(request_otp, username=config["user"])
        ctx.invoke(login, username=config["user"], otp=None)
        ctx.invoke(change_forwarding_email, email=email, tries=tries + 1)
        return
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
