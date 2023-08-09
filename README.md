# LightsRadExtractor
Simple console application to extract lights.rad information that was used to compile the source 1 engine map. This app should work for all bsp's of a version 20 and 21, but was tested mostly for games such as CS:GO and CS:S. Formerly it was known as a ``lrfind`` or ``lightradfinder``.

## Usage
If you plan on building or using the app directly from python:
* Make sure to have python 3.10.2 (might support lower versions, but untested) or higher installed;
* Clone this repository;
* Run ``python3 lightsradextractor.py path/to/bspfile.bsp``;
* Gathered lights.rad information would be printed to console as well as file ``lights_<bspfilename>.rad`` would be created near the .bsp that was used on;

Alternatively you can use a standalone executable, that you can download [here](https://github.com/GAMMACASE/LightsRadExtractor/releases), then drag & drop the .bsp file onto it or run it via cmd like ``lightsradextractor.exe path/to/bspfile.bsp``.

Console output and produced file will contain the information in a format ``path/to/texture R G B``, where ``R G B`` will be represented as numbers which are already scaled by the overall intensity. In simple words the text output won't match the exact inputs that were used when map was compiled, but the light properties and its intensity would match 100% to the original if compiled within the same game and same compiling options.

You can also run the app with a ``-h`` to see its available additional arguments that might produce different results in case the app doesn't finds all the textures.

> **NOTE:** Textures that weren't used on the map at the compile stage would not be recoverable, so you won't get them generated in the produced output.

> **NOTE:** Don't add **4th** value to the generated list, as the ``R G B`` values that are generated are **already scaled** by the correct amount, so adding any number besides 255 as an intensity scale (4th number) would produce a non-matching scene to the original.
