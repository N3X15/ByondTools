=================
0.1.1c - 6/10/2014
=================

* Missed data directory.  Whoops.
* Object tree: Fixed mishandling of list() in variables when [ is on the same line.

=================
0.1.1b - 6/2/2014
=================

* Fixed some leftover packaging issues:

  * post-install didn't create self-executables on Linux, so just calling dmi, dmmfix, etc. wouldn't work.
  * setup.py didn't specify sub-packages for installation, so installations were fairly broken.
 
* Post-install process now uses sys.executable, rather than trying to figure it out via hackier means.
* README changed to reStructuredText for eventual pip release.
* Oh my god there's a changelog now
* Added MANIFEST.in (fixed a problem uploading *.rst files).
