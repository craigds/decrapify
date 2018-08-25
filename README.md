# Some examples of how to use Bowler

[Bowler](https://pybowler.io/) is a Facebook incubator project for refactoring Python code using lib2to3.

This is hopefully going to be a collection of shortish scripts, each doing a simple refactor on the source files you give it.

Currently, there's only one, and it's usable but far from feature complete.

Requires Python 3.6.

# fstrings.py {sourcefile.py}

Upgrades source file to use f-strings wherever possible. i.e. converts this

```python
'%s string literal' % myvar
```
into this:

```python
f'{myvar} string literal'
```

# Warning

This repo exists primarily as a learning exercise. You should exercise care (or, run away!) if trying to using these scripts on code that is dear to you.

# Requirements

Python 3.6+
The other stuff in `requirements.txt`

# Install

```bash
git clone git@github.com:craigds/pybowler-examples.git
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```
