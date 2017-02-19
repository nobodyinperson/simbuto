# Simbuto

**Simbuto** is a simple graphical budgeting tool.

**Note**: This application is definitely usable, but still in early development. More features are to follow. Feel free to fork this repository, make your changes and then file a Pull Request.

## What can it do?

You tell **Simbuto** at which points in time you have what costs and income and it creates a graph showing you your total assets over time in the future.

## What does it look like?

A screenshot of **Simbuto** in action:

![simbuto screenshot](https://cloud.githubusercontent.com/assets/19148271/23094767/426c00f0-f5ff-11e6-8947-c51f30d1546e.png)

On the left-hand side there is an **editor** where you can specify what **income** and **costs** you have at which time or intervals. With this information, the **graph** on righ right-hand side is created. It shows your **assets over time** in the future with **worst/best case scenario** and **ensemble quantiles** depending on the temporal and monetary tolerances you specified.

## Debian package

There are ready-to-use debian packages on the [releases page](https://github.com/nobodyinperson/simbuto/releases), you may download the [latest release](https://github.com/nobodyinperson/simbuto/releases/latest) there.

For automatic updates, you may use my [apt repository](http://apt.nobodyinperson.de).

To build a debian package from the repository, run ```dpkg-buildpackage -us -uc``` (options mean without signing) from the repository root.
There will be a ```simbuto_*.deb``` one folder layer above.

## Installation

Install the debian package via ```sudo dpkg -i simbuto_*.deb```. If you get errors mentioning unconfigured packages, install the remaining dependencies via ```sudo apt-get install -f```. 
Older versions of **simbuto** will automatically be removed.

If you use my [apt repository](http://apt.nobodyinperson.de), install **simbuto** like any other package via ```sudo apt-get update && sudo apt-get install simbuto```

## What languages are available?

At the moment, these are the available translations:

- English
- German
- French (incomplete)
- Swedish (incomplete)

The application decides on what language it chooses based on the current locale, i.e. the `LANG` environment variable.

## Background

I really like [GnuCash](http://gnucash.org/) for keeping an eye on my finances. It is awesome to make sure everything in the past or near future is okay with your money. But GnuCash lacks a good feature to see what will happen in "far" future, say a year for example. That's why I created **Simbuto**.

## What's behind the scenes?

**Simbuto** uses:

- **R** to create the graphs
- **GTK** as graphical user interface
- **Python** to organize and glue everything together

## Special thanks

- The awesome people who develop [**GTK**](https://www.gtk.org/), [Gnu **R**](https://www.r-project.org/),[the python module **rpy2**](https://rpy2.bitbucket.io/) and [**Python**](https://www.python.org/) of course
- Ascot on [StackOverflow.com](http://stackoverflow.com/a/26457317/5433146) for a workaround on ```signal.signal(signal, handler)``` when using a ```GLib.MainLoop```
