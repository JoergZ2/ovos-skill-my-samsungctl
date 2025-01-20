# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/> My Samsung Tv Rc
A skill for remote control some Samsung TV by OVOS

## About
My OVOS Samsung TV skill is developed and tested with the ue55es6760 model. whether the skill works with other tvs needs to be tried.

For control, the python library samsungctl is required, which will be installed by setup.py

## Examples
* "TV (television) next channel"
* "TV channel three"
* "TV program guide" - calls the program guide and starts a dialog for using the cursor by voice

## Skill configuration (settings.json)
* "tv": IP of your Samsung TV
* "port": 55000 (default)
* "placement": Room  (optional)
* "method": legacy (for greatest compatibility)
* "rc_name": (virtual) Name of voice RC
* "description": Description (optional)
* "translations" Language localization of cursor control and confirming selection or escaping a menu

Localization: Write the words without spaces after the comma, for example, in German: links,rechts,nach oben,nach unten,nehmen,verlassen. The spaces between 'nach' and 'oben' is ok. Today there is a localization for German only.

## Credits
JoergZ2

## Category
**Entertainment**
Media

## Tags
#OVOS, Remote control, tv, television, samsung
