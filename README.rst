====================
LensMemoriae
====================

.. |badge_license| image:: https://img.shields.io/badge/license-LGPL--3-blue.png
    :alt: License: LGPL-3

.. |badge_github| image:: https://img.shields.io/badge/github-tonica%2Flensmemoriae-lightgray.png?logo=github
    :target: https://github.com/tonica/lensmemoriae/tree/19.0
    :alt: tonica/lensmemoriae

|badge_license| |badge_github|

Recover the memory of your photographs: manage, tag, moderate, geolocate and
share images from Odoo, with a public gallery, self-registration and facial
recognition.

This repository aggregates Odoo 19 addons:

+-----------------------+------------------------------------------------+-------------+
| Addon                 | Summary                                        | Installable |
+=======================+================================================+=============+
| lensmemoriae          | Recover the memory of photographs              | Yes         |
+-----------------------+------------------------------------------------+-------------+
| lensmemoriae_faces    | Automatic face detection and person grouping   | Yes         |
+-----------------------+------------------------------------------------+-------------+

The ``lensmemoriae`` addon is an application (its own menu appears in the main
apps menu); ``lensmemoriae_faces`` extends it and is not an application.

Each addon ships an OCA-style ``README.rst`` generated from ``readme/``
fragments; open them for full details.

Installation
============

This repository is intended to be used with `git-aggregator
<https://github.com/acsone/git-aggregator>`_ (Doodba / OCA project
scaffolding). The addons depend on a running Odoo 19 instance and, for the
faces addon, on the optional ``face_recognition`` and ``numpy`` Python
packages.

Usage / Configuration
=====================

See the per-addon documentation:

* `lensmemoriae <lensmemoriae/README.rst>`_
* `lensmemoriae_faces <lensmemoriae_faces/README.rst>`_

Development conventions
=======================

* Each addon keeps its documentation in ``readme/*.rst`` fragments
  (``DESCRIPTION``, ``USAGE``, ``CONFIGURE``, ``ROADMAP``, ``HISTORY``,
  ``CONTRIBUTORS``).
* The generated ``README.rst`` files are produced with
  ``oca-gen-addon-readme`` and must be regenerated whenever the fragments
  change.
* **Every commit that changes a module must also update the corresponding
  ``readme`` fragments and regenerate the ``README.rst``.**

License
=======

This project is released under the `LGPL-3
<https://www.gnu.org/licenses/lgpl-3.0.html>`_ license. See the ``LICENSE``
file for details.
