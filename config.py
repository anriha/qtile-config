from typing import List  # noqa: F401
import math
import os
import subprocess
from glob import glob
import random

from libqtile import bar, layout, widget, hook
from libqtile.log_utils import logger
from libqtile.config import Click, Drag, Group, Key, Screen
from libqtile.lazy import lazy
from libqtile.core.manager import Qtile
from Xlib import display as xdisplay
from nvidia_sensors import NvidiaSensors

mod = "mod4"
terminal = "alacritty"


@hook.subscribe.startup_once
def autostart():
    autostart = os.path.expanduser("~/.config/qtile/autostart.sh")
    subprocess.call([autostart])


def get_num_monitors():
    num_monitors = 0
    try:
        display = xdisplay.Display()
        screen = display.screen()
        resources = screen.root.xrandr_get_screen_resources()

        for output in resources.outputs:
            monitor = display.xrandr_get_output_info(output, resources.config_timestamp)
            preferred = False
            if hasattr(monitor, "preferred"):
                preferred = monitor.preferred
            elif hasattr(monitor, "num_preferred"):
                preferred = monitor.num_preferred
            if preferred:
                num_monitors += 1
    except Exception as _:
        return 1
    else:
        return num_monitors


num_monitors = get_num_monitors()


def take_screenshot(qtile):
    os.system("maim -s --format=png /dev/stdout | xclip -selection clipboard -t image/png -i")


def get_closest(x, y, clients):
    """Get closest window to a point x,y"""
    target_min = None
    target_idx = None

    for idx, target in enumerate(clients):
        value = math.hypot(target.info()["x"] - x, target.info()["y"] - y)
        if target_min is None or value < target_min:
            target_min = value
            target_idx = idx

    if target_min is None:
        return None, None
    return target_idx, clients[target_idx]


def focus_smart(qtile: Qtile, key):
    win = qtile.current_window
    x, y = win.x, win.y
    screens = qtile.screens
    candidates = []
    screens_helper = []
    for screen in screens:
        group = screen.group
        layout = group.layout
        for c in layout.clients:
            if key == "h":
                if c.info()["x"] < x:
                    candidates.append(c)
                    screens_helper.append(screen)
            elif key == "j":
                if c.info()["y"] < y:
                    candidates.append(c)
                    screens_helper.append(screen)
            elif key == "k":
                if c.info()["y"] > y:
                    candidates.append(c)
                    screens_helper.append(screen)
            elif key == "l":
                if c.info()["x"] > x:
                    candidates.append(c)
                    screens_helper.append(screen)


    selected_idx, selected = get_closest(x, y, candidates)
    if selected is None:
        return
    selected_screen = screens_helper[selected_idx]
    qtile.focus_screen(selected_screen.index)
    selected_screen.group.layout.group.focus(selected)

    # qtile.current_group.focus(qtile.current_layout.current_client)


keys = [
    # Switch between windows in current stack pane
    Key([mod], "h", lazy.function(focus_smart, "h")),
    Key([mod], "j", lazy.function(focus_smart, "j")),
    Key([mod], "k", lazy.function(focus_smart, "k")),
    Key([mod], "l", lazy.function(focus_smart, "l")),
    # Move windows up or down in current stack
    Key([mod, "control"], "k", lazy.layout.shuffle_up(), desc="Move window down in current stack "),
    Key([mod, "control"], "j", lazy.layout.shuffle_down(), desc="Move window up in current stack "),
    Key([mod, "control"], "l", lazy.layout.shuffle_right(), desc="Move window up in current stack "),
    Key([mod, "control"], "h", lazy.layout.shuffle_left(), desc="Move window up in current stack "),
    # Switch window focus to other pane(s) of stack
    Key([mod], "space", lazy.layout.next(), desc="Switch window focus to other pane(s) of stack"),
    # Swap panes of split stack
    Key([mod, "shift"], "space", lazy.layout.rotate(), desc="Swap panes of split stack"),
    Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod, "shift"], "f", lazy.window.toggle_floating()),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle between split and unsplit sides of stack"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
    Key([mod, "control"], "r", lazy.restart(), desc="Restart qtile"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown qtile"),
    Key([mod], "r", lazy.spawn("dmenu_run"), desc="Spawn a dmenu_run launcher"),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ +5%")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ -5%")),
    Key([], "Print", lazy.function(take_screenshot)),
]

groups = []


def switch_on_screen(qtile, key):
    screen = qtile.current_screen
    screen_idx = screen.index
    screen.set_group(qtile.groups_map[key + str(screen_idx)])
    # .group[key + str(0)].toscreen()


def switch_to_screen(qtile, key):
    screen = qtile.current_screen
    screen_idx = screen.index
    qtile.current_window.togroup(key + str(screen_idx))


for s in "1234567890":
    for i in range(num_monitors):
        spawn = None
        if s == "1":
            if i in [0, 2]:
                spawn = "brave"
            else:
                spawn = "rambox"

        group = Group(s + str(i), label=s, spawn=spawn, screen_affinity=i)
        groups.append(group)
        keys.append(Key([mod], s, lazy.function(switch_on_screen, s)))
        keys.append(Key([mod, "shift"], s, lazy.function(switch_to_screen, s)))

# for i in groups:
#     keys.extend(
#         [
#             # mod1 + letter of group = switch to group
#             Key([mod], i.name, lazy.group[i.name].toscreen(), desc="Switch to group {}".format(i.name)),
#             # mod1 + shift + letter of group = switch to & move focused window to group
#             Key(
#                 [mod, "shift"],
#                 i.name,
#                 lazy.window.togroup(i.name, switch_group=True),
#                 desc="Switch to & move focused window to group {}".format(i.name),
#             ),
#             # Or, use below if you prefer not to switch to that group.
#             # # mod1 + shift + letter of group = move focused window to group
#             # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
#             #     desc="move focused window to group {}".format(i.name)),
#         ]
#     )

layouts = [
    layout.MonadTall(margin=10, single_margin=0, border_width=0),
    layout.Max(),
    layout.Stack(num_stacks=2),
    # Try more layouts by unleashing below layouts.
    # layout.Columns(),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

widget_defaults = dict(
    font="sans",
    fontsize=24,
    padding=3,
)
extension_defaults = widget_defaults.copy()


screens = []

wallpaper_images = glob(os.path.expanduser("~/wallpapers/") + "*")
wallpaper_image = random.choice(wallpaper_images)

for screen_id in range(num_monitors):
    screen = Screen(
        wallpaper=wallpaper_image,
        wallpaper_mode="fill",
        bottom=bar.Bar(
            [
                widget.GroupBox(visible_groups=[a + str(screen_id) for a in "1234567890"]),
                widget.Spacer(length=50),
                widget.WindowName(),
                widget.Spacer(),
                widget.Volume(),
                widget.Spacer(length=50),
                widget.Net(format="{down} ↓↑ {up}"),
                widget.Spacer(length=50),
                widget.TextBox(text="CPU: "),
                widget.ThermalSensor(tag_sensor="Tdie"),
                widget.CPU(format=" {load_percent}%"),
                widget.Spacer(length=50),
                widget.Memory(format="RAM: {MemPercent}%"),
                widget.Spacer(length=50),
                NvidiaSensors(format="GPU: {temp}°C {util}"),
                widget.Spacer(length=50),
                widget.Clock(format="%Y-%m-%d %a %H:%M"),
            ],
            28,
        ),
    )
    screens.append(screen)


# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None  # WARNING: this is deprecated and will be removed soon
follow_mouse_focus = False
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        {"wmclass": "confirm"},
        {"wmclass": "dialog"},
        {"wmclass": "download"},
        {"wmclass": "error"},
        {"wmclass": "file_progress"},
        {"wmclass": "notification"},
        {"wmclass": "splash"},
        {"wmclass": "toolbar"},
        {"wmclass": "confirmreset"},  # gitk
        {"wmclass": "makebranch"},  # gitk
        {"wmclass": "maketag"},  # gitk
        {"wname": "branchdialog"},  # gitk
        {"wname": "pinentry"},  # GPG key password entry
        {"wmclass": "ssh-askpass"},  # ssh-askpass
        *layout.Floating.default_float_rules,
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"


# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"


@hook.subscribe.client_new
def floating_size_hints(window):
    hints = window.window.get_wm_normal_hints()
    if hints and 0 < hints["max_width"] < 1000:
        window.floating = True
