// Posted by BYOND devs on their forums.

//directions
var/const
    NORTH     =  1
    SOUTH     =  2
    EAST      =  4
    WEST      =  8
    NORTHEAST =  5
    NORTHWEST =  9
    SOUTHEAST =  6
    SOUTHWEST = 10
    UP        = 16
    DOWN      = 32

//mob sight bits
var/const
    BLIND     =  1
//  SEE_INVIS =  2
    SEE_MOBS  =  4
    SEE_OBJS  =  8
    SEE_TURFS = 16
    SEE_SELF  = 32
    SEE_INFRA = 64

//for backwards compatibility
#define SEEINVIS 2
#define SEEMOBS 4
#define SEEOBJS 8
#define SEETURFS 16

//client perspective settings
var/const
    MOB_PERSPECTIVE = 0
    EYE_PERSPECTIVE = 1

//elevations
var/const
    FLOAT_LAYER = -1
    AREA_LAYER =   1
    TURF_LAYER =   2
    OBJ_LAYER  =   3
    MOB_LAYER  =   4
    FLY_LAYER  =   5

//movement animation
#define NO_STEPS      0
#define FORWARD_STEPS 1
#define SLIDE_STEPS   2
#define SYNC_STEPS    3

//booleans
var/const
    TRUE  = 1
    FALSE = 0

//genders
var/const
    MALE = "male"
    FEMALE = "female"
    NEUTER = "neuter"
    PLURAL = "plural"

//cursors
var/const
    MOUSE_INACTIVE_POINTER = 0
    MOUSE_ACTIVE_POINTER   = 1
    MOUSE_DRAG_POINTER     = 3
    MOUSE_DROP_POINTER     = 4
    MOUSE_ARROW_POINTER    = 5
    MOUSE_CROSSHAIRS_POINTER = 6
    MOUSE_HAND_POINTER     = 7

//system types
var/const
    MS_WINDOWS = "MS Windows"
    UNIX = "UNIX"

#define ASSERT(condition) \
if(!(condition)) { \
   CRASH("[__FILE__]:[__LINE__]:Assertion Failed: [#condition]"); \
}

//some _dm_interface flags  (keep in sync with dmval.h)
#define _DM_datum   0x001
#define _DM_atom    0x002
#define _DM_movable 0x004
#define _DM_sound   0x020
#define _DM_Icon    0x100
#define _DM_RscFile 0x200

sound
    var
        file
        repeat
        wait
        channel

    _dm_interface = _DM_datum|_DM_sound|_DM_RscFile

    New(file,repeat,wait,channel)
        src.file = fcopy_rsc(file)
        src.repeat = repeat
        src.wait = wait
        src.channel = channel
        return ..()
    proc
        RscFile()
            return file

//icon blending functions
#define ICON_ADD 0
#define ICON_SUBTRACT 1
#define ICON_MULTIPLY 2
#define ICON_OVERLAY  3

icon
    _dm_interface = _DM_datum|_DM_Icon|_DM_RscFile
    var/icon
    New(icon,icon_state,dir)
        src.icon = _dm_new_icon(icon,icon_state,dir)
    proc
        Icon()
            return icon
        RscFile()
            return fcopy_rsc(icon)

        IconStates()
            return icon_states(icon)
        Turn(angle)
            _dm_turn_icon(icon,angle)
        Flip(dir)
            _dm_flip_icon(icon,dir)
        Shift(dir,offset,wrap)
            _dm_shift_icon(icon,dir,offset,wrap)
        SetIntensity(r,g=-1,b=-1)
            _dm_icon_intensity(icon,r,g,b)
        Blend(icon,function)
            _dm_icon_blend(src.icon,icon,function)
        SwapColor(old_rgb,new_rgb)
            _dm_icon_swap_color(icon,old_rgb,new_rgb)