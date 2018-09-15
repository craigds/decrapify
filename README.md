# decrapify

This is a set of scripts which refactor your Python code. They're invocations of [Bowler](https://pybowler.io/), which is a Facebook incubator project for refactoring Python code using lib2to3.

These scripts are just assorted refactoring steps I've found helpful in my day job as a full time Python developer, that I was unable to find elsewhere.

Please suggest or contribute extra scripts. I will accept any high quality scripts that may be useful, even if they're not useful to *me*. If you have a cool idea, please open an issue.

# fstrings.py {sourcefile.py}

Upgrades source file to use f-strings wherever possible. i.e. converts this

```python
'%s string literal' % myvar
```
into this:

```python
f'{myvar} string literal'
```

# pytestify.py {sourcefile.py}

*Partially* converts your xunit-style tests to pytest ones. Doesn't get you all the way there, but reduces the effort required to manually finish the job.

# Warning

This repo exists primarily as a learning exercise in concrete syntax trees. You should exercise care if trying to using these scripts on code that is dear to you.

# Requirements

Python 3.6+
The other stuff in `requirements.txt`

# Install

```bash
git clone git@github.com:craigds/decrapify.git
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```
