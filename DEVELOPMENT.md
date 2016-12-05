For development purposes, you will sometimes need to change some code and try it.
This should happen without changing the main installation of `temper-python`.
Here is how to do it.

You will need these tools installed:

- `git`
- `python` (if you don't know which, grab Python 3)
- `virtualenv` for the Python version (see below)

# Clone the repository

This will clone into a directory named `temper-dev`:

```
pa@plug2:~/temper$ git clone https://github.com/padelt/temper-python.git temper-dev
Cloning into 'temper-dev'...
remote: Counting objects: 544, done.
Receiving objects: 100% (544/544), 118.51 KiB, done.
remote: Total 544 (delta 0), reused 0 (delta 0), pack-reused 544
Resolving deltas: 100% (329/329), done.
pa@plug2:~/temper$ cd temper-dev/
pa@plug2:~/temper/temper-dev$
```

# How to find `virtualenv`

A virtualenv basically isolates all the package installation we are going to do
in a subdirectory instead of the global python repository.

Unfortunately, availability of virtualenv differs greatly between Python versions.

In Python 2 and until 3.3, this is a seperate tool, usually installed from your distribution
packages and available as a binary named `virtualenv` (check availability using
`which virtualenv`).

In Python 3.4+, we finally reached a sane solution: Virtualenv is a module in
the standard Python distribution and is called using `python -m venv` followed
by your desire virtualenv directory.

# Setting up a `virtualenv` and activating it

Check which python binary is available and what you want by entering `python`
and hitting the Tab key twice to have your shell suggest some:

```
pa@plug2:~/temper/temper-dev$ python
python            python2.7         python3           python3.2mu       python-config
python2           python2.7-config  python3.2         python3mu
```

I will choose `python3.2`.


To have it set up in the subdirectory `venv` (the name could be any valid
directory name), try this:

```
pa@plug2:~/temper/temper-dev$ virtualenv -p python3.2 venv
Running virtualenv with interpreter /usr/bin/python3.2
New python executable in venv/bin/python3.2
Also creating executable in venv/bin/python
Installing setuptools, pip, wheel...done.
pa@plug2:~/temper/temper-dev$ ll venv/bin/
insgesamt 2792
-rw-r--r-- 1 pa pa    2242 Dez  5 11:34 activate
-rw-r--r-- 1 pa pa    1268 Dez  5 11:34 activate.csh
-rw-r--r-- 1 pa pa    2481 Dez  5 11:34 activate.fish
-rw-r--r-- 1 pa pa    1137 Dez  5 11:34 activate_this.py
-rwxr-xr-x 1 pa pa     262 Dez  5 11:34 easy_install
-rwxr-xr-x 1 pa pa     262 Dez  5 11:34 easy_install-3.2
-rwxr-xr-x 1 pa pa     234 Dez  5 11:34 pip
-rwxr-xr-x 1 pa pa     234 Dez  5 11:34 pip3
-rwxr-xr-x 1 pa pa     234 Dez  5 11:34 pip3.2
lrwxrwxrwx 1 pa pa       9 Dez  5 11:34 python -> python3.2
lrwxrwxrwx 1 pa pa       9 Dez  5 11:34 python3 -> python3.2
-rwxr-xr-x 1 pa pa 2814320 Dez  5 11:34 python3.2
-rwxr-xr-x 1 pa pa     241 Dez  5 11:34 wheel
pa@plug2:~/temper/temper-dev$
```

Now activate it:

```
pa@plug2:~/temper/temper-dev$ . venv/bin/activate
(venv)pa@plug2:~/temper/temper-dev$
```

What this does is prepend your PATH environment variable to prefer the python
executable in the virtualenv. All the installations using `pip` will now go
there and not into your global python repo.

To later deactivate it, run `deactivate` (which is a function set into your
running `bash` by `activate`).

Check that the right python binary will be called:

```
(venv)pa@plug2:~/temper/temper-dev$ which python
/home/pa/temper/temper-dev/venv/bin/python
```

Great!

# Install `temper-python` into the virtualenv

```
(venv)pa@plug2:~/temper/temper-dev$ python setup.py install
running install
...
Installing temper-poll script to /home/pa/temper/temper-dev/venv/bin
...
Finished processing dependencies for temperusb==1.5.2
(venv)pa@plug2:~/temper/temper-dev$
```

Now we can run `temper-poll` for testing. Since the virtualenv is active,
our fresh install is found first:
```
(venv)pa@plug2:~/temper/temper-dev$ which temper-poll
/home/pa/temper/temper-dev/venv/bin/temper-poll
(venv)pa@plug2:~/temper/temper-dev$ temper-poll
Found 2 devices
Device #0: 30.9°C 87.7°F
Device #1: 17.1°C 62.8°F
(venv)pa@plug2:~/temper/temper-dev$
```

# Development/testing workflow

To test a change, you need to follow this workflow:

- Make your changes to e.g. `temperusb/temper.py`
- Run `python setup.py install --force` (the `--force` will have it
  reinstalled despite the package version in `setup.py` not changing).
- Run `temper-poll`

This is a simple and surefire way to deal with module names and
dependencies.
