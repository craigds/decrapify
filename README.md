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

# :warning: Warning

This repo exists primarily as a learning exercise in concrete syntax trees. You should exercise care if trying to using these scripts on code that is dear to you.

# Requirements

Python 3.6+
The other stuff in `requirements.txt`

# Future ideas?

Some ideas I had which I haven't implemented yet:

 * convert `super(X,  self)` to `super()` (assuming X matches the class def)
 * remove obsolete `__future__` import statements (do any of the existing futurize/modernize tools do this? I couldn't find any)
 * re-format/prettify docstrings in some circumstances. (black doesn't touch the contents of docstrings). Specifically I would probably:
     - always use """triple-double-quotes"""
     - always put both start and end quotes on their own line
     - always match the indenation of the quotes to each other
     - always use a raw string if the docstring contains a backslash
     - always indent content to at least the same level as the starting quote marks.

# Install

```bash
git clone git@github.com:craigds/decrapify.git
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```
