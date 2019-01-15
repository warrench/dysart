# DySART (Dynamic Settings and Retrieval Toolkit) &mdash; enabling introspection for EQuS

I think the picture of what this package is supposed to do is _starting_ to
come into focus. The meat of DySART should consist of a set of extensible fitting tools, a measurement dependency and precedence resolution algorithm, and a job scheduler,
as well a number of (yet undefined) interfaces to a database system, an instrument controller and users.

The exact scope of the package is a pretty open question. It might end up as a fairly lean set of core utilities,
or as a more fully-featured system. This is something to feel out and discuss as the needs of the lab
and the lab workflow become more clear. The exact relationship to Labber and Labber Quantum is also an open
question, but one probably not worth resolving until there is more substance here.

## (Semi-)stable features

### Config script
The config script in the top-level directory auto-handles setup for dysart
development. Usage is as follows:

* To run setup, navigate to the dysart top-level directory and run `$ . config
on`. The script searches for a python environment management tool (currently,
either conda or virtualenv) and initializes a new environment called `dysenv`
(Make sure you don't already have an environment with this name!) and installs
all dependencies that can be found on PyPI (currently, everything except for
Labber). It also creates a directory  subtree for the debug database is one is
not found.
After the first usage, this command simply activates the environment and runs
the database server.

* To deactivate the development environment and kill the database server, run
`$ . config off`. This feature shouldn't interfere with other mongodb servers
running on your machine, but exercise caution.

* To update requirements, run `$ . config update`. This feature is probably not
very reliable. It might cause code regression, and I wouldn't trust it in a
life-or-death situation. 

* To perform a hard reset, run `$ . config clean`. This turns everything off,
clears the database and uninstalls the python environment. Note that this
feature is not strictly safe: if your working directory has similarly named
subdirectories to `dysart/`, they might end up getting recursively deleted! You
will be warned about this if you try to do it, but you're being warned about it
here, too.

## Desiderata
* Interface to existing Labber-based measurement tools
* Unified fitting tools based on lmfit API
    * Emphasis on robustness. Should operate reliably and predictably on any conceivable real data from the experiments.
* High-level abstractions for device characterization and device data management
* Command line tools for measurement
  * e.g. `$tuneup fridge1/chip1/qb1` to update resonator frequencies, inter-qubit crosstalk; ![](.img/pi.gif)-pulse, ![](.img/T1T2.gif)...
  * intelligently handle calibration dependencies
  * log calibration snapshots or deltas referenced to existing log files

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
