# DySART (Dynamic Settings and Retrieval Toolkit) &mdash; enabling introspection for EQuS

I think the picture of what this package is supposed to do is _starting_ to come into focus. The meat of DySART should consist
of a set of extensible fitting tools, a measurement dependency and precedence resolution algorithm, and a job scheduler,
as well a number of (yet undefined) interfaces to a database system, an instrument controller and users.

The exact scope of the package is a pretty open question. It might end up as a fairly lean set of core utilities,
or as a more fully-featured system. This is something to feel out and discuss as the needs of the lab
and the lab workflow become more clear. The exact relationship to Labber and Labber Quantum is also an open
question, but one probably not worth resolving until there is more substance here.

Here are some desiderata subject to review:
* Interface to existing Labber-based measurement tools
* Unified fitting tools based on lmfit API
    * Emphasis on robustness. Should operate reliably and predictably on any conceivable real data from the experiments.
* High-level abstractions for device characterization and device data management
* Command line tools for measurement
  * e.g. `$tuneup fridge1/chip1/qb1` to update resonator frequencies, inter-qubit crosstalk; ![](.img/pi.gif)-pulse, ![](.img/T1T2.gif)...
  * intelligently handle calibration dependencies
  * log calibration snapshots or deltas referenced to existing log files

Where we don't want to reinvent the wheel:
* Labber backend
  * Labber's plotting capabilities
  * .hdf5 specification
  * Database? I'm not actually clear on this. What to do here depends on how/where data is currently hosted. Personally, I find the idea of saving a bunch of hand-titled .json files in some directory somewhere on a local machine to be a little kludgy. We can probably do better, but I'm not sure if that's actually how things are currently done.
* Writing our own fitting library. Should use established tools like lmfit.

Stretch goals and/or wish items that might be downright silly:
* Compatibility with quantum programming environment: either home-brewed or commercial or open-source tools:
	* pyQuil
	* LIQUi|>
	* QISKit
  * Quipper
  * etc.
* Web interface? It might be pretty cool to run experiments remotely from a browser, and it would be a fun excuse to learn `trendywebframework.js`. Eventually, could even open up to public along the lines of commercial cloud QC offerings (for ++publicity and therefore ++funding), preferably coincident with a major paper release. There are more than a few catches, though, including that this opens up a host of security issues that didn't exist before, that it might require updating server hardware, etc.
* Integration with Slack?
