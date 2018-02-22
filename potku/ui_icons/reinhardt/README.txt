This is The Reinhardt Icon Set

- This icon set has been created for use with the Reinhardt Style available from the kde-look site at ( www.kde-look.org ), and is a proposal for the default Slicker icon set.
- This is an SVG icon set. This means that it requires at least KDE 3.2 (if you use anything less, it's really silly of you ;) ). If you want to use the icon set as a PNG set, this is still possible, though it will take you a little while to make it one such. Run the makeiconset.sh script (not the makesvgdistro.sh which is for my personal use mainly) and wait (run it in console to get some verbose output about what it's doing). After this process has completed, swap the two files index.desktop and index.desktop.png around so they are called index.desktop.svg and index.desktop respectively. You should now have a working PNG icon set. Note that this requires Inkscape to be installed as well as ImageMagick.
- If you wish to have the icons a different colour, this is possible by selecting the Icons section of the Control Panel, then selecting Advanced. Here you can set the effect used on all the icons, one of which is Colouration. (thanks to spooq for this tip)
- If you want to use these icons, please give credit where due. They are released under the GNU Lesser General Public License (LGPL) (available from www.gnu.org/copyleft ).
- The icon set is based on an original concept by Alexander Smith.

Please note that at least on my machine, the libart included with Konstruct for KDE 3.3.2 destroys the kde icon renderer to the extent that using Reinhardt will crash most applications as well as render most of the icons utterly weirdly.
The way to fix this is to use the makeiconfolder.sh script included with the SVG package to render the SVG files to PNG. Install Sodipodi and run the script from the base of the icon folder (probably ~/.kde/share/icons/reinhardt-0.10/) and wait a while... A rather long while, I'm afraid, it takes a long time to render that many icons.
If you do not have crashy type problems and the icons look fine, there is no need to do this!

Programs used:
Sodipodi ( http://sodipodi.sourceforge.net )
InkScape
( http://www.inkscape.org )
ImageMagick ( http://www.imagemagick.org )

Personal Homepage: http://www.leinir.dk/

On the name:
Ad Reinhardt, 1913-1967
Reinhardt was an American minimalist painter, who became known for his extreme style, which also became more and more reductive from the mid 1950s, towards his death in 1967. After 1955 he worked almost exclusively in near-black. This said, there is in fact colour in the paintings, for example his "Abstract Painting no. 5", 1962, which can be found at the Tate Modern ( www.tate.org.uk ), is, though seemingly black-blue, in fact squared with blue and red.

~ Dan // Leinir



Changelog:
Version 0.10
+ The total number of icons is now 1361
+ 141 New or severely edited icons in all sections
+ Icons added to make Amarok 1.4 icon complete
+ Icons containing representations of text have been edited heavily for
speed and clarity (no more squinting at your toolbars!)

Version 0.9.3
+ The total number of icons is now 1269
+ 164 New or severely edited icons in all section
+ Icons added to work with KDE 3.4, and most application icons are now there
+ Added TODO list for icons (please tell me if there's any missing ones ;) )
+ A few icons by Stefan Fritsch added
+ Add icons to complete amaroK's look again
+ Changed the scripts over to using Inkscape in stead of Sodipodi


Version 0.9.2
+ The total number of icons is now 1116
+ 189 New or severely edited icons in all sections
+ Edited most icons to get the superfluous gradient definitions removed
+ Fixed a few problems with the index.desktop file (it might even be faster)
+ Begin adding icons for supporting the new KDE Icon support in the GTK-QT theme
+ Simplify some of the icons (notably the text ones, to make toolbars render much faster in programs like Kopete and KWord, where the formatting toolbars were very slow)
+ Add support for http://www.kde-apps.org/content/show.php?content=15045
+ Add and rename icons for use with KDE 3.3
+ Fix display problems with Kopete status icons (they are now composited on the run by Kopete)
