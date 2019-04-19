# DySART (Dynamic Settings and Retrieval Toolkit) &mdash; enabling introspection for EQuS

I think the picture of what this package is supposed to do is _starting_ to
come into focus. The meat of DySART should consist of a set of extensible fitting tools, a measurement dependency and precedence resolution algorithm, and a job scheduler,
as well a number of (yet undefined) interfaces to a database system, an instrument controller and users.

Note that many features in this package depend on using python 3. The
configuration script will attempt to use python 3.7.

## Installation

In its current state, DySART is equally supported on MacOS and Linux (it has
been tested on Ubuntu and Arch Linux). It should also work on Windows, modulo
any undiscovered filesystem navigation bugs. However, the configuration script,
which also contains some simple utilities that will be useful to developers, is
written for bash, so it might only work correctly on unix systems.

To install DySART, first ensure that you have the right requirements installed.
You will first need python 3.7 and a python virtual environment system
(conda and virtualenv are currently supported). You should then install MongoDB
if you want to use the database facilities. This can be done on MacOS with
homebrew (`$ brew install mongodb`) or from the website. Most non-esoteric Linux
package managers (including apt and pacman) should also supply an up-to-date
version of MongoDB.

To set up the database and python environment, enter the top-level `dysart`
directory and run `$ . config` in bash (unfortunately, other shells are
currently unsupported.) It is imperative that you run this command verbatim
in this directory. Follow the prompts, and it should set up all the
components for you, including the python virtual environment, python packages,
and skeletons of the database and log. Among other prompts, you will be asked
for permission to modify your `.bashrc` or `.bash_profile.` This modification
will alias the dysart scripts to `dys`, which for the time being I've
considered the least-invasive installation option.
If the installation succeeds, you should now be able to run other dysart
commands with `$ dys <command>` from any working directory.

If you want to use Labber facilities, you can link DySART to your Labber
installation by running `$ dys labber /path/to/Labber`.

Now you should be all set. To see what the software can do, you can try some
simple virtual qubit measurements. Run a Labber InstrumentServer serving a
Single-Qubit Simulator and a Multi-Qubit Pulse Generator, and try running the
following example:

<p align="center">
  <img src="assets/dys_example.png" alt="qubit measurement example" />
</p>

## (Semi-)stable features

### Config script
The config script in the top-level directory auto-handles setup for dysart
development. Usage is as follows:

* To run setup, navigate to the dysart top-level directory and run `$ dys on`. The script searches for a python environment management tool (currently,
either conda or virtualenv) and initializes a new environment called `dysenv`
(Make sure you don't already have an environment with this name!) and installs
all dependencies that can be found on PyPI (Note to virtualenv users: tk will
not be supported, and must be provided by your system's python installation).
It also creates a directory  subtree for the debug database if one is not found.
After the first usage, this command simply activates the environment and runs
the database server.

* To deactivate the development environment and kill the database server, run
`$ dys off`. This feature shouldn't interfere with other mongodb servers
running on your machine, but exercise caution.

* To update requirements, run `$ dys update`. This feature is probably not
very reliable. It might cause code regression, and I wouldn't trust it in a
life-or-death situation.

* To make Labber's python API available to DySART, run `$ dys labber
path/to/Labber`. This feature can also be used to update the location of a
Labber installation that has been moved, or to switch to a new Labber installation.

* To perform a hard reset, run `$ dys clean`. This turns everything off,
clears the database and uninstalls the python environment. Note that this
feature is not strictly safe: if your working directory has similarly named
subdirectories to `dysart/`, they might end up getting recursively deleted! You
will be warned about this if you try to do it, but you're being warned about it
here, too. You can do a more controlled clean with `$ . config clean env`, `$
dys clean log` or `$ dys clean db`, which wipe the python environment,
database log, and whole database, respectively.

* To see a list of commands, run `$ dys` or `$ dys help`.

### DyPy interpreter setup
Under Dysart, a special $PYTHONSTARTUP script is run to provide the user a
consistent interavtive programming environment. At the moment, this
script connects to a default database and Labber InstrumentServer,
and making these assets accessible to the other system components.

### Dummy measurements
The "dummy lab" in `dysart/measurements` provides a model of some of the
desired end-state functionality. This virtual lab setting provides a collection
of instruments and instrument controllers to take various measurements, and
show how DySART writes the results to a database and logs its progress. For a
brief demonstration, run `$ python dysart/measurement/dummy_measurement.py`.
The progress of the experiments will be sent to stdout and the results saved to
the MongoDB database at `debug_data/db`.

## Tests
There's a collection of tests in `dysart/tests` which should pass before every
commit. They haven't been packaged up neatly yet with any more sophisticated
testing tools, but can be run by hand with `$ python example_test.py`. If
you're Conda on MacOS, you will need to install pythonw (e.g. by `$ conda
install python.app`)` for the tests to run. Unforunately, I've been adding
features faster than I've been adding tests, but generally a feature should not
be considered stable until a test exists for it.

## Incomplete and missing features.
Windows support will almost certainly be necessary in the near future, and
currently doesn't exist. In particular, the config script is written for bash,
so the python environment and database will currently have to be configured
manually on a Windows machine.

## Desiderata
* High-level abstractions for device characterization and device data management
* Command line tools for measurement
  * e.g. `$ tuneup fridge1/chip1/qb1` to update resonator frequencies,
  * inter-qubit crosstalk; ![](assets/pi.gif)-pulse, ![](assets/T1T2.gif)...

### Where we don't want to reinvent the wheel
* Labber backend
  * Labber's plotting capabilities
  * .hdf5 specification
  * Database? I'm not actually clear on this. What to do here depends on how/where data is currently hosted. Personally, I find the idea of saving a bunch of hand-titled .json files in some directory somewhere on a local machine to be a little kludgy. We can probably do better, but I'm not sure if that's actually how things are currently done.
* Writing our own fitting library. Should use established tools like lmfit.

### Stretch goals that might be downright silly
* Compatibility with quantum programming environment: either home-brewed or commercial or open-source tools:
	* pyQuil
	* LIQUi|>
	* QISKit
  * Quipper
  * etc.
* Web interface? It might be pretty cool to run experiments remotely from a browser, and it would be a fun excuse to learn `trendywebframework.js`. Eventually, could even open up to public along the lines of commercial cloud QC offerings (for ++publicity and therefore ++funding), preferably coincident with a major paper release. There are more than a few catches, though, including that this opens up a host of security issues that didn't exist before, that it might require updating server hardware, etc.
* Integration with Slack?
