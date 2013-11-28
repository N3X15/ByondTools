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
	var/list/contents=list() 
	var/density=0 
	var/desc="" 
	var/dir=2 
	var/gender="neutral" 
	//var/icon
	//var/icon_state
	var/invisibility=0 
	var/list/underlays=list() 
	var/list/overlays=list() 
	var/loc=null 
	var/layer=3 
	var/mouse_over_pointer 
	var/mouse_drag_pointer 
	var/mouse_drop_pointer 
	var/mouse_drop_zone 
	var/mouse_opacity 
	var/name="" 
	var/opacity=1 
	var/pixel_x=0 
	var/pixel_y=0 
	var/pixel_z=0 
	var/text="" 
	var/list/verbs 
	var/x=0 
	var/y=0 
	var/z=0 