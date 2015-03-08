.. Copyright (c) Moshe Zadka
   See LICENSE for details.

Synopsis
=========

EXPERIMENTAL EXPERIMENTAL EXPERIMENTAL
YOU SHOULD PROBABLY NOT USE IT IN PRODUCTION!!!
THIS CODE IS EXTREMELY UNTESTED

NColony: Infrastructure for running "colonies" of processes.

Hacking
===========

In order to start hacking, run

.. code-block:: bash

  $ ./admin/setup-dev
  $ . ./build/env/bin/activate

This will put the shell into a Python virtual
environment which is suitable for development.

For testing and building:

.. code-block:: bash

  $ python setup.py all

Code changes where this command does not finish
successfully are almost certain not to be merged
as-is.

It is recommended to occasionally do

.. code-block:: bash

  $ deactivate
  $ git clean -dxf
  $ ./admin/setup-dev
  $ . ./build/env/bin/activate
  $ python setup.py all

In order to make sure that a clean repository
builds cleanly.

Code Example
=============

Assuming an environment where 'pip install ncolony' has been done

.. code-block:: bash

  $ DEFAULT="--config config --messages messages"
  $ twistd ncolony $DEFAULT
  $ python -m ncolony.ctl $DEFAULT add sleeper --cmd=/bin/sleep --arg=10
  $ python -m ncolony.ctl $DEFAULT restart sleeper


API Reference
==============

While not existing publically, after building, the API reference
will be in build/sphinx/html/index.html

Contributors
=============

Moshe Zadka <zadka.moshe@gmail.com>

License
=======

MIT License