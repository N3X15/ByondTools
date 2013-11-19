/**
* OpenBYOND Standard Library: atom defaults
*
* This file defines the default state of datums.
*/

/
	var/list/vars=list()
	var/type=null
	var/parent_type=null

/atom
	var/list/contents=list() //List of contents. Closets store their contents in this var as do all storage items. All the items on a turf are in the turf's contents var.
	var/density=0 //If density is at 0, you can walk over the object, if it's set to 1, you can't.
	var/desc="" //Description. When you right-click and examine an object, this will show under the name.
	var/dir=2 //Object direction. Sprites have a direction variable which can have 8 'legal' states. More info
	var/gender="neutral" //not used
	//var/icon //The dmi file where the sprite is saved. Must be written in single quotations (Example: 'items.dmi')
	//var/icon_state //The name of the sprite in the dmi file. If it's not a valid name or is left blank, the sprite without a name in the dmi file will be used. If such a sprite doesn't exist it will default to being blank.
	var/invisibility=0 //Invisibility is used to determine what you can and what you can't see. Check the code or wait for someone who knows how exactly this works to write it here.
	var/list/underlays=list() //List of images (see image() proc) which are underlayed under the current sprite
	var/list/overlays=list() //List of images (see image() proc) which are overlayed over the current sprite
	var/loc=null //Contains a reference to the turf file where the object currently is.
	var/layer=3 //A numerical variable which determins how objects are layered. Tables with a layer of 2.8 are always under most items which have a layer of 3.0. Layers go up to 20, which is reserved for HUD items.
	var/mouse_over_pointer //not used
	var/mouse_drag_pointer //(almost) not used
	var/mouse_drop_pointer //not used
	var/mouse_drop_zone //not used
	var/mouse_opacity //Used in a few places. Check the description in the reference page
	var/name="" //The name of the object which is displayed when you right click the object and in the bottom left of the screen when you hover your mouse over it.
	var/opacity=1 //Whether you can see through/past it (glass, floor) when set to 0 or whether you can't (walls, mecha) when set to 1.
	var/pixel_x=0 //How many pixels in the x direction should the sprite be offset from the starting set. See the APC's New() proc for an example and how fire alarms are defined on the map. pixel_x = -5 will move it 5 pixels to the left and pixel_x = 5 will move it 5 pixels to the right
	var/pixel_y=0 //Same as pixel_y but in the y direction. Positive values move it to the north, negative to the south.
	var/pixel_z=0 //Used in isometric maps, so it's not used in SS13
	var/text="" //How to represent the object on text clients. Not used.
	var/list/verbs //The verbs you can use with the item. Verbs are the options in the right click menu.
	var/x=0 //X position, read only. Set the loc variable to move it or use the inbulit functions.
	var/y=0 //Y position, read only.
	var/z=0 //Z position (Which z-level it's on), read only.