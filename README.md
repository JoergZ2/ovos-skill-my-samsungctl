# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/> My Samsung Tv Rc
A skill for remote control some samsung tvs by mycroft

## About
My samsung tv Mycroft.ai skill is developed and tested with the ue55es6760 model. whether the skill works with other tvs needs to be tried.

for control, the python library samsungctl is required, which must be installed in the virtual environment of mycroft e.g.:

## Examples
* "TV (television) next channel"
* "TV channel three"
* "TV program guide" - calls the program guide and starts a dialog for using the cursor by voice

## Skill configuration (home.mycroft.ai)
* Standard TV: IP of your Samsung TV
* Port: 55000 (default)
* Placement: Room  (optional)
* Method: legacy (for greatest compatibility)
* Name: (virtual) Name of voice RC
* Description: Description (optional)
* Your words for...: Localization of cursor control and confirming selection or escaping a menu

Localization: Write the words without spaces after the comma, for example, in German: links,rechts,nach oben,nach unten,nehmen,verlassen. The spaces between 'nach' and 'oben' is ok. Today there is a localization for German only.

## Credits
JoergZ2

## Category
**Entertainment**
Media

## Tags
#Remote control, tv, television, samsung
