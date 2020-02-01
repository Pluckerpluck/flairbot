# FlairBot

A simple bot that manages the flairs for /r/brawlhalla

## Config

Under `config.yml` you can set:

* `overrides`: Any individual overrides you with to apply:
    * The key must match the filename of the flair

## Running

Using Python 3 first create a virtual environment and enter it:

```bash
$ python -m venv venv
$ ./venv/Scripts/activate
```

Followed by installing the requirements:

```bash
(venv) $ pip install -r requirements.txt
```

And finally running the code:

```bash
(venv) $ python -m flairbot.spritesheet
```

The generate files can be found in `./dist/`
