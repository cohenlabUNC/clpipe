============
Installation
============

Installation of clpipe is fairly simple. If you have priviledges to add python packages to a system, you can install the most recent version of clpipe with

.. code-block:: console

    pip3 install --upgrade git+git://github.com/cohenlabUNC/clpipe

If you don't have access to the global library (perhaps you are just a user of an HPC), you can install a local copy by adding the ``--user`` flag.

.. code-block:: console

     pip3 install --user --upgrade git+git://github.com/cohenlabUNC/clpipe

The installation command may print out warnings, which are fine:

.. code-block:: console

    WARNING: You are using pip version 19.2.3, however version 19.3.1 is available.
    You should consider upgrading via the 'pip install --upgrade pip' command.

The installation will also install any additional packaged needed.

If you don't already have a Singularity image of fMRIprep, head over to their `site <https://fmriprep.readthedocs.io/en/latest/index.html>`_ and follow the directions. You will have to change the fMRIprep image path in your configuration file.

Similarly, if you do not have a copy of the BIDS-validator Singularity image, go ahead and construct one.

Once these images are available, clpipe is ready to go.

-----------------------
A Note for UNC-CH Users
-----------------------

If you are a Longleaf user, and a member of the hng posix group, you already have access to the latest singularity images for both fmriprep and the bids validator, so there is no need to construct your own, unless you want a older version.

---------------
Batch Languages
---------------

clpipe was originally designed for use on University of North Carolina at Chapel Hill's HPC, Longleaf, which uses the SLURM task management system. The way clpipe handles what batch language to use is through a set of batch configuration files. These files are not directly exposed to users, and modification of these directly is ill advised. For other institutions that use task management systems other than SLURM, get in touch with the package maintainers, and we would be happy to help setup a configuration file for your system. In coming versions of clpipe, functionality will be added to allow users to change the batch management system settings.

