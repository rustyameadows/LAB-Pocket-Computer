"""LAB Studio's GTK 4 desktop workbench. Run with the system Python on Linux."""
import io
import keyword
import math
import os
import sys
import time
import tokenize
from pathlib import Path

from PIL import Image, ImageDraw
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gsk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gdk, Gio, GLib, Graphene, Gsk, Gtk, Pango

from engine import FPS, Game, GameError
from pocket_keys import BOARD
from studio_store import RevisionConflict, Store, StoreError


ACTION_KEYS = {
    "left": "←", "right": "→", "up": "↑", "down": "↓",
    "a": "Z", "b": "X", "start": "Enter", "select": "Shift",
}
ACTION_NUMBER = {action: number for number, action in BOARD.items()}
CAPS = {"left": "←", "right": "→", "up": "↑", "down": "↓",
        "a": "A", "b": "B", "start": "▶", "select": "◇"}
KEYS = {
    Gdk.KEY_Left: "left", Gdk.KEY_Right: "right", Gdk.KEY_Up: "up", Gdk.KEY_Down: "down",
    Gdk.KEY_z: "a", Gdk.KEY_x: "b", Gdk.KEY_Return: "start",
    Gdk.KEY_KP_Enter: "start", Gdk.KEY_Shift_L: "select", Gdk.KEY_Shift_R: "select",
}
CART_KINDS = {
    "falling-blocks": "Falling blocks", "snake": "Grid chase",
    "breakout": "Paddle arcade",
}


def box(vertical=False, spacing=0, css=None):
    widget = Gtk.Box(
        orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL,
        spacing=spacing,
    )
    if css:
        widget.add_css_class(css)
    return widget


def pad(widget, horizontal, vertical=None):
    vertical = horizontal if vertical is None else vertical
    widget.set_margin_start(horizontal)
    widget.set_margin_end(horizontal)
    widget.set_margin_top(vertical)
    widget.set_margin_bottom(vertical)
    return widget


def label(text, css=None, wrap=False):
    widget = Gtk.Label(label=text, xalign=0)
    if css:
        widget.add_css_class(css)
    if wrap:
        widget.set_wrap(True)
        widget.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    else:
        widget.set_ellipsize(Pango.EllipsizeMode.END)
    return widget


def space():
    spacer = Gtk.Box()
    spacer.set_hexpand(True)
    return spacer


def button(text, callback, css="secondary-action", icon=None):
    widget = Gtk.Button()
    widget.add_css_class(css)
    content = box(spacing=6)
    content.set_halign(Gtk.Align.CENTER)
    if icon:
        content.append(Gtk.Image.new_from_icon_name(icon))
    if text:
        content.append(label(text))
    widget.set_child(content)
    widget.connect("clicked", lambda *_: callback())
    return widget


def texture(image):
    image = image.convert("RGB")
    return Gdk.MemoryTexture.new(
        image.width, image.height, Gdk.MemoryFormat.R8G8B8,
        GLib.Bytes.new(image.tobytes()), image.width * 3,
    )


def cart_art(template, size=38):
    """Small hand-drawn pixel icons for the individual cartridge spines."""
    bg, fg, detail = {
        "snake": ("#a9d5af", "#244e3f", "#ed724a"),
        "breakout": ("#bcb5df", "#493765", "#ffe396"),
        "logo": ("#c9f67d", "#25352b", "#25352b"),
    }.get(template, ("#e8cc80", "#836439", "#424b36"))
    img = Image.new("RGB", (38, 38), bg)
    pen = ImageDraw.Draw(img)

    def block(x, y, w, h, shade):
        pen.rectangle((x, y, x+w-1, y+h-1), fill=shade)

    if template == "logo":
        for x,y,w,h in [(7,7,5,23), (12,25,6,5), (17,7,5,14), (22,7,6,5), (26,12,5,9), (22,18,6,5)]:
            block(x,y,w,h,fg)
    elif template == "snake":
        for x, y in [(6,23), (12,23), (18,23), (18,17), (18,11), (24,11)]:
            block(x,y,6,6,fg)
        block(8,8,4,4,detail)
    elif template == "breakout":
        for r in range(2):
            for c in range(3):
                block(5+c*10,7+r*6,8,4,fg if r == 0 else detail)
        block(13,28,14,3,fg)
        block(22,21,3,3,fg)
    else:
        for x,y in [(5,25),(11,25),(17,25),(17,19),(23,25),(29,25),(29,19),(11,7),(17,7),(17,13),(23,13)]:
            block(x,y,5,5,fg if y>14 else detail)
    art = Gtk.Picture.new_for_paintable(texture(img.resize((size,size), Image.Resampling.NEAREST)))
    art.set_size_request(size, size)
    art.set_can_shrink(False)
    art.set_valign(Gtk.Align.CENTER)
    return art


def rectangle(x, y, w, h):
    return Graphene.Rect().init(x, y, w, h)


def rgba(code):
    shade = Gdk.RGBA()
    shade.parse(code)
    return shade


class Monitor(Gtk.Widget):
    def __init__(self):
        super().__init__(hexpand=True, vexpand=True)
        self.surface = None
        self.set_size_request(250,245)
        self.shades = [rgba(c) for c in ("#e0e5d8", "#c4cebf", "#bbc5b4", "#37453a", "#18291e")]

    def frame(self, image):
        self.surface = texture(image)
        self.queue_draw()

    def do_snapshot(self, snapshot):
        w, h = self.get_width(), self.get_height()
        snapshot.append_color(self.shades[0], rectangle(0, 0, w, h))
        if w <= 0 or h <= 0:
            return
        snapshot.push_repeat(rectangle(0,0,w,h), rectangle(0,0,14,14))
        snapshot.append_color(self.shades[1], rectangle(9,9,1,1))
        snapshot.pop()
        avail = min(w-42,h-36)
        if avail < 1:
            return
        scale = max(1, int(avail/160)) if avail >= 160 else avail/160
        size = 160 * scale
        x, y = math.floor((w-size)/2), math.floor((h-size)/2)
        snapshot.append_color(self.shades[2], rectangle(x-9,y-5,size+18,size+18))
        snapshot.append_color(self.shades[3], rectangle(x-9,y-9,size+18,size+18))
        snapshot.append_color(self.shades[4], rectangle(x-4,y-4,size+8,size+8))
        if self.surface is not None:
            snapshot.append_scaled_texture(self.surface, Gsk.ScalingFilter.NEAREST, rectangle(x,y,size,size))


class StudioWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="LAB Studio")
        self.add_css_class("studio")
        self.set_default_size(1100, 735)
        self.set_size_request(800, 555)
        self.store = Store()
        self.project = None
        self.game = None
        self.playing = False
        self.dirty = False
        self.drafts = {}
        self.library_version = None
        self.selecting = False
        self.loading = False
        self.held = set()
        self.pulse = set()
        self.highlights = set()
        self.lights = {}
        self.led_style = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(self.get_display(), self.led_style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        self.playback_time = 0
        self.space_down = False
        self.clock = time.monotonic()
        self.skip_close_confirm = False
        self.highlight_timer = 0
        self.build_ui()
        self.connect("close-request", self.on_close)
        self.connect("notify::is-active", lambda *_: self.clear_keys() if not self.is_active() else None)
        self.poll()
        self.poll_timer = GLib.timeout_add(600, self.poll)
        self.frame_timer = GLib.timeout_add(15, self.tick)

    def build_ui(self):
        header = Gtk.HeaderBar()
        header.add_css_class("studio-header")
        # Works with system window buttons on either side.
        header.set_title_widget(Gtk.Box())
        brand = box(spacing=9)
        brand.set_valign(Gtk.Align.CENTER)
        brand.append(cart_art("logo",30))
        brand.append(label("LAB Studio","brand"))
        version = label("v0","version")
        version.set_valign(Gtk.Align.CENTER)
        brand.append(version)
        header.pack_start(brand)
        header.pack_end(button("New game",self.new_game,"new-cart","list-add-symbolic"))
        self.export_btn = button("Export",self.export,"top-action","document-save-as-symbolic")
        header.pack_end(self.export_btn)
        header.pack_end(button("Import", self.import_cartridge, "top-action", "document-open-symbolic"))
        self.set_titlebar(header)
        shell = box();self.set_child(shell)
        shelf = box(True,0,"shelf");shelf.set_size_request(204,-1);shelf.set_hexpand(False);shell.append(shelf)
        shelf_top = pad(box(spacing=5),17,18);shelf.append(shelf_top)
        library_heading=label("CARTRIDGES","overline");library_heading.set_ellipsize(Pango.EllipsizeMode.NONE);shelf_top.append(library_heading);shelf_top.append(space())
        self.cart_count=label("0","number");shelf_top.append(self.cart_count)
        self.library = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.library.add_css_class("shelf-list")
        self.library.connect("row-selected",self.choose_row)
        shelf_scroll = Gtk.ScrolledWindow()
        shelf_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        shelf_scroll.set_vexpand(True);shelf_scroll.set_child(self.library);shelf.append(shelf_scroll)
        foot = box(True,8,"shelf-footer");shelf.append(foot)
        inside = pad(box(True,8),14,14);foot.append(inside)
        inside.append(button("MCP connection",self.bridge,"bridge-button","network-wired-symbolic"))
        inside.append(label("Local workspace","shelf-caption"))

        desk = box(True,0,"desk");desk.set_hexpand(True);shell.append(desk)
        paper = pad(box(True,12),22,16);paper.set_vexpand(True);desk.append(paper)
        heading = box(spacing=8);paper.append(heading)
        titles = box(True,2);titles.set_hexpand(True);heading.append(titles)
        self.game_title = label("LAB Pocket","game-name");titles.append(self.game_title)
        self.description = label("","description",True);self.description.set_max_width_chars(75);titles.append(self.description)
        self.remix_btn = button("Remix",self.remix,"top-action","edit-copy-symbolic")
        self.remix_btn.set_valign(Gtk.Align.START);heading.append(self.remix_btn)
        nav = box(spacing=8);paper.append(nav)
        modes = box(css="mode-bar");nav.append(modes)
        self.tabs = {}
        for name,title in [("play","Playtest"),("source","Source")]:
            tab = Gtk.ToggleButton(label=title)
            tab.add_css_class("mode-tab")
            if self.tabs:tab.set_group(self.tabs["play"])
            tab.connect("toggled",self.change_mode,name);modes.append(tab);self.tabs[name]=tab
        nav.append(space()); self.rev_note=label("","caption");nav.append(self.rev_note)
        self.notice_row=box(spacing=5,css="notice");self.notice_row.set_visible(False);paper.append(self.notice_row)
        self.notice_text=label("","description",True);self.notice_text.set_hexpand(True);self.notice_row.append(self.notice_text)
        dismiss=button("",lambda:self.notice_row.set_visible(False),"minor-action","window-close-symbolic")
        dismiss.set_tooltip_text("Dismiss message");self.notice_row.append(dismiss)
        self.pages=Gtk.Stack(vexpand=True,hexpand=True)
        self.pages.set_vhomogeneous(False)
        paper.append(self.pages)
        self.pages.add_named(self.play_page(),"play")
        self.pages.add_named(self.source_page(),"source")
        self.tabs["play"].set_active(True)
        status=pad(box(spacing=8,css="statusbar"),0,0);desk.append(status)
        inner=pad(box(spacing=8),16,5);inner.set_hexpand(True);status.append(inner)
        self.status_msg=label("Ready","footer-meta");inner.append(self.status_msg);inner.append(space())
        inner.append(label("POCKET SIMULATOR","footer-meta"))
        keys=Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed",self.keyboard_down);keys.connect("key-released",self.keyboard_up)
        self.add_controller(keys)

    def play_page(self):
        area=box(spacing=12)
        stage=box(True,0,"stage");stage.set_hexpand(True);stage.set_vexpand(True);area.append(stage)
        head=box(spacing=5,css="stage-head");stage.append(head)
        strip=pad(box(spacing=5),11,9);strip.set_hexpand(True);head.append(strip)
        strip.append(label("POCKET DISPLAY","stage-tag"));strip.append(space())
        strip.append(label("160 × 160","caption"))
        self.monitor=Monitor();stage.append(self.monitor)
        transport=box(css="stage-foot");stage.append(transport)
        strip=pad(box(spacing=7),10,7);strip.set_hexpand(True);transport.append(strip)
        self.play_btn=button("Play",self.toggle_play,"primary-action","media-playback-start-symbolic");strip.append(self.play_btn)
        reset=button("",self.reset,"secondary-action","view-refresh-symbolic");reset.set_tooltip_text("Restart game");strip.append(reset)
        strip.append(space());self.meter=label("","caption");strip.append(self.meter)

        rail=box(True,0,"rail");rail.set_size_request(190,-1);rail.set_hexpand(False);area.append(rail)
        scroll=Gtk.ScrolledWindow(vexpand=True);scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);rail.append(scroll)
        content=pad(box(True,10),12,14);scroll.set_child(content)
        content.append(label("Controls","rail-title"))
        self.bindings=box(True,5);content.append(self.bindings)
        sep=Gtk.Separator();sep.add_css_class("section-rule");content.append(sep)
        content.append(label("Pocket keypad","rail-title"))
        self.key_grid=Gtk.Grid(column_spacing=3,row_spacing=3,column_homogeneous=True)
        content.append(self.key_grid);self.caps={}
        for i in range(1,21):
            action=BOARD.get(i)
            cap=Gtk.Button(label=CAPS[action] if action else str(i).zfill(2))
            cap.add_css_class("keycap");cap.set_name(f"lab-key-{i:02}");cap.set_can_focus(False)
            cap.set_tooltip_text(f"Key {i:02}" + (f" · {action}" if action else ""))
            click=Gtk.GestureClick();click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            click.connect("pressed",self.pad_press,i);click.connect("released",self.pad_release,i)
            click.connect("cancel",lambda _,seq,n=i:self.release_number(n))
            cap.add_controller(click)
            self.key_grid.attach(cap,(i-1)%5,(i-1)//5,1,1)
            self.caps[i]=cap
        return area

    def source_page(self):
        pane=box(True,0,"source-pane")
        head=box(spacing=6,css="source-head");pane.append(head)
        head.append(label("main.py","file-label"));head.append(space())
        head.append(button("Reload",self.ask_reload,"minor-action"))
        head.append(button("Save & run",self.save,"primary-action","media-playback-start-symbolic"))
        self.editor=Gtk.TextView(monospace=True,top_margin=12,left_margin=12,right_margin=10,bottom_margin=12)
        self.editor.set_wrap_mode(Gtk.WrapMode.NONE);self.editor.add_css_class("code")
        self.buffer=self.editor.get_buffer();self.buffer.connect("changed",self.source_changed)
        for name,shade in {"keyword":"#815328","string":"#477233","comment":"#748276","number":"#5d5595"}.items():
            self.buffer.create_tag(name,foreground=shade)
        scroller=Gtk.ScrolledWindow(vexpand=True,hexpand=True);scroller.set_child(self.editor);pane.append(scroller)
        return pane

    def message(self,text,error=False):
        self.notice_text.set_text(text);self.notice_row.set_visible(True)
        if error:self.notice_row.add_css_class("error")
        else:self.notice_row.remove_css_class("error")

    def change_mode(self,tab,mode):
        if not tab.get_active() or not hasattr(self,"pages"):return
        self.pages.set_visible_child_name(mode)
        self.clear_keys()
        if mode=="source":
            self.set_playing(False);self.editor.grab_focus()

    def clear_keys(self):
        self.held.clear();self.pulse.clear()
        self.space_down = False
        if hasattr(self,"caps"):self.paint_caps()

    def list_rows(self,items):
        self.selecting=True
        try:
            while child:=self.library.get_first_child():self.library.remove(child)
            for item in items:
                row=Gtk.ListBoxRow();row.project_id=item["id"]
                line=pad(box(spacing=8),8,8)
                template=item.get("template") or item["id"]
                line.append(cart_art(template))
                names=box(True,2);names.set_valign(Gtk.Align.CENTER);names.set_hexpand(True)
                name=label(item["title"],"cart-name");name.set_max_width_chars(18);names.append(name)
                names.append(label(CART_KINDS.get(template,"Game cartridge"),"cart-kind"))
                line.append(names);row.set_child(line);self.library.append(row)
            self.cart_count.set_text(str(len(items)).zfill(2))
            self.select_row(self.project["id"] if self.project else None)
        finally:self.selecting=False

    def select_row(self,ident):
        row=self.library.get_first_child()
        while row:
            if row.project_id==ident:
                self.library.select_row(row);return
            row=row.get_next_sibling()

    def choose_row(self,_,row):
        if not row or self.selecting or (self.project and row.project_id==self.project["id"]):return
        try:
            self.store.set_active(row.project_id)
            self.load(self.store.get_project(row.project_id))
        except (StoreError,OSError) as exc:self.message(str(exc),True)

    def poll(self):
        try:
            state=self.store.workspace_status()
            if self.library_version!=state["library_version"]:
                self.list_rows(self.store.list_projects());self.library_version=state["library_version"]
            ident=state["active_id"]
            if ident and (self.project is None or ident!=self.project["id"]):
                self.load(self.store.get_project(ident))
            elif ident and state["revision"]!=self.project["revision"]:
                if self.dirty:
                    if getattr(self,"last_notice_revision",None)!=state["revision"]:
                        self.message("This game changed through MCP. Remix to keep your draft, or reload the saved source.",True)
                        self.last_notice_revision=state["revision"]
                else:self.load(self.store.get_project(ident))
        except (StoreError,OSError) as exc:self.message(str(exc),True)
        return GLib.SOURCE_CONTINUE

    def load(self,project,restore=True):
        if self.project and self.dirty:
            self.drafts[self.project["id"]]=(self.source(),self.project["revision"])
        self.project=dict(project);self.set_title(project["title"]+" · LAB Studio")
        self.last_notice_revision=None;self.loading=True
        self.set_playing(False);self.clear_keys()
        self.game_title.set_text(project["title"])
        self.description.set_text(project["description"])
        self.notice_row.set_visible(False)
        draft=self.drafts.get(project["id"]) if restore else None
        self.buffer.set_text(draft[0] if draft else project["source"])
        self.dirty=draft is not None and draft[0]!=project["source"]
        if self.dirty:
            self.project["revision"]=draft[1]
            self.message("Restored your unsaved source. Save & run to preview it.")
        self.update_rev()
        self.selecting=True;self.select_row(project["id"]);self.selecting=False
        self.build_bindings(project.get("controls",{}))
        self.loading=False;self.schedule_highlight()
        self.install_preview(project["source"])
        self.status_msg.set_text("Preview ready" if self.game else "Source needs attention")

    def build_bindings(self,controls):
        while child:=self.bindings.get_first_child():self.bindings.remove(child)
        for name,desc in controls.items():
            row=box(spacing=4); key=label(ACTION_KEYS.get(name,name),"binding")
            row.append(key); text=label(str(desc),"input-action",True);text.set_hexpand(True)
            row.append(text);self.bindings.append(row)
        for i,cap in self.caps.items():
            if BOARD.get(i) in controls or f"key{i:02}" in controls:cap.add_css_class("mapped")
            else:cap.remove_css_class("mapped")

    def install_preview(self,source):
        try:self.game=Game(source,seed=1);self.draw_frame()
        except (GameError,ValueError) as exc:
            self.game=None;self.monitor.surface=None;self.monitor.queue_draw()
            self.meter.set_text("Stopped");self.message(str(exc),True)
        self.play_btn.set_sensitive(self.game is not None)

    def update_rev(self):
        self.rev_note.set_text(f"rev {self.project['revision']:02d}"+("  ·  unsaved" if self.dirty else ""))

    def source(self):
        start,end=self.buffer.get_bounds();return self.buffer.get_text(start,end,True)

    def source_changed(self,*_):
        if self.loading or not self.project:return
        self.dirty=self.source()!=self.project["source"]
        if not self.dirty:self.drafts.pop(self.project["id"],None)
        self.update_rev();self.schedule_highlight()

    def schedule_highlight(self):
        if self.highlight_timer:GLib.source_remove(self.highlight_timer)
        self.highlight_timer=GLib.timeout_add(190,self.highlight)

    def highlight(self):
        self.highlight_timer=0
        if not self.project:return False
        text=self.source()
        self.buffer.remove_all_tags(*self.buffer.get_bounds())
        if len(text)>96000:return False
        try:
            for token in tokenize.generate_tokens(io.StringIO(text).readline):
                tag={tokenize.STRING:"string",tokenize.COMMENT:"comment",tokenize.NUMBER:"number"}.get(token.type)
                if token.type==tokenize.NAME and keyword.iskeyword(token.string):tag="keyword"
                if tag:
                    ok,start=self.buffer.get_iter_at_line_offset(token.start[0]-1,token.start[1])
                    ok2,end=self.buffer.get_iter_at_line_offset(token.end[0]-1,token.end[1])
                    if ok and ok2:self.buffer.apply_tag_by_name(tag,start,end)
        except (tokenize.TokenError,IndentationError,SyntaxError):pass
        return False

    def save(self):
        if not self.project:return
        try:
            code=self.source()
            candidate=Game(code,seed=1);candidate.step(())
            if self.dirty:
                data=self.store.update_project(self.project["id"],code,self.project["revision"])
            else:data=self.store.get_project(self.project["id"])
            self.dirty=False;self.drafts.pop(data["id"],None)
            self.load(data,restore=False);self.tabs["play"].set_active(True);self.set_playing(True)
            self.status_msg.set_text("Saved and running")
        except RevisionConflict:
            self.message("The saved revision changed. Remix to keep this draft or Reload to use the new revision.",True)
        except (StoreError,GameError,ValueError,OSError) as exc:self.message(str(exc),True)

    def ask_reload(self):
        if not self.project:return
        def reload_now():
            self.dirty=False;self.drafts.pop(self.project["id"],None)
            self.load(self.store.get_project(self.project["id"]),restore=False)
        if self.dirty:self.confirm("Reload saved source?","Your edits in this draft will be discarded.","Reload",reload_now)
        else:reload_now()

    def set_playing(self,playing):
        self.playing=bool(playing and self.game)
        self.clock=time.monotonic();self.playback_time=0
        if not hasattr(self,"play_btn"):return
        content=box(spacing=5);content.set_halign(Gtk.Align.CENTER)
        icon="media-playback-pause-symbolic" if self.playing else "media-playback-start-symbolic"
        content.append(Gtk.Image.new_from_icon_name(icon));content.append(label("Pause" if self.playing else "Play"))
        self.play_btn.set_child(content)
        if hasattr(self,"status_msg") and self.game:self.status_msg.set_text("Running" if self.playing else "Paused")

    def toggle_play(self):
        if self.game:self.set_playing(not self.playing)

    def reset(self):
        if not self.project:return
        was=self.playing;self.clear_keys();self.install_preview(self.project["source"]);self.set_playing(was)
        self.status_msg.set_text("Restarted")

    def press_number(self,num):
        names={f"key{num:02d}"};action=BOARD.get(num)
        if action:names.add(action)
        if not self.playing and self.game:self.set_playing(True)
        self.held.update(names);self.pulse.update(names);self.paint_caps()

    def release_number(self,num):
        self.held.discard(f"key{num:02d}");self.held.discard(BOARD.get(num));self.paint_caps()

    def pad_press(self,gesture,n,x,y,num):
        self.press_number(num)

    def pad_release(self,gesture,n,x,y,num):
        self.release_number(num)

    def keyboard_down(self,_,key,code,state):
        if state&Gdk.ModifierType.CONTROL_MASK and Gdk.keyval_to_lower(key)==Gdk.KEY_s:
            self.save();return True
        if self.pages.get_visible_child_name()!="play":return False
        if key==Gdk.KEY_space and not state&Gdk.ModifierType.CONTROL_MASK:
            if not self.space_down:
                self.space_down = True
                self.toggle_play()
            return True
        action=KEYS.get(Gdk.keyval_to_lower(key))
        if action:
            if action not in self.held:self.press_number(ACTION_NUMBER[action])
            return True
        return False

    def keyboard_up(self,_,key,code,state):
        if key == Gdk.KEY_space:
            self.space_down = False
        action=KEYS.get(Gdk.keyval_to_lower(key))
        if action:self.release_number(ACTION_NUMBER[action])

    def paint_caps(self):
        for n,cap in self.caps.items():
            for cls,active in (("lit",f"key{n:02}" in self.highlights),("held",f"key{n:02}" in self.held)):
                if active:cap.add_css_class(cls)
                else:cap.remove_css_class(cls)

    def draw_frame(self):
        self.monitor.frame(self.game.image());state=self.game.inspect()
        self.meter.set_text(f"Score  {state.get('score',0)}")
        observed=state.get("keys",{})
        lit=set(k for k,v in observed.items() if v) if isinstance(observed,dict) else set(observed or ())
        if observed != self.lights:
            self.lights = observed.copy()
            swatches = []
            for number in range(1, 21):
                shade = observed.get(f"key{number:02}")
                if shade:
                    swatches.append(f"button#lab-key-{number:02} {{ box-shadow: inset 0 -4px {shade}; }}")
            self.led_style.load_from_string("\n".join(swatches))
        if lit != self.highlights:
            self.highlights = lit
            self.paint_caps()

    def tick(self):
        if not self.playing or not self.game:return True
        now=time.monotonic()
        self.playback_time=min(.12,self.playback_time+now-self.clock);self.clock=now
        advanced=False
        try:
            while self.playback_time>=1/FPS:
                self.game.step(self.held|self.pulse);self.pulse.clear()
                self.playback_time-=1/FPS;advanced=True
            if advanced:self.draw_frame()
        except (GameError,ValueError) as exc:
            self.set_playing(False);self.message(str(exc),True)
        return True

    def confirm(self,title,detail,action,callback):
        dialog=Gtk.AlertDialog(message=title,detail=detail,buttons=["Cancel",action])
        dialog.set_default_button(0);dialog.set_cancel_button(0)
        def done(d,result,*_):
            try:
                if d.choose_finish(result)==1:callback()
            except GLib.Error:pass
        dialog.choose(self,None,done)

    def title_dialog(self,title,default,submit,templates=None):
        dialog=Gtk.Window(transient_for=self,modal=True,title=title,resizable=False)
        dialog.set_default_size(360,-1)
        panel=pad(box(True,12,"dialog-content"),20)
        dialog.set_child(panel)
        panel.append(label(title,"dialog-title"))
        panel.append(label("Cartridge title","overline"))
        field=Gtk.Entry(text=default);field.set_activates_default(True);panel.append(field)
        selector=None
        if templates:
            panel.append(label("Starting game","overline"))
            selector=Gtk.DropDown.new_from_strings([t["title"] for t in templates])
            selector.set_selected(next((i for i, t in enumerate(templates) if t["id"] == "falling-blocks"), 0))
            panel.append(selector)
        error=label("","description",True);error.set_visible(False);panel.append(error)
        def accept():
            name=field.get_text().strip()
            try:
                if not name:raise ValueError("Enter a title.")
                template=templates[selector.get_selected()]["id"] if selector else None
                submit(name,template)
            except (ValueError,OSError) as exc:
                error.set_text(str(exc));error.set_visible(True);return
            dialog.close()
        actions=box(spacing=7);actions.set_halign(Gtk.Align.END);panel.append(actions)
        actions.append(button("Cancel",dialog.close))
        create=button("Create game" if templates else "Create remix",accept,"primary-action")
        actions.append(create);dialog.set_default_widget(create)
        dialog.present();field.grab_focus();field.select_region(0,-1)

    def new_game(self):
        templates=self.store.list_templates()
        if not templates:
            self.message("There are no sample templates available.",True);return
        def create(title,template):
            item=self.store.create_project(title,template)
            self.poll();self.load(item)
            self.tabs["play"].set_active(True);self.status_msg.set_text("Created game")
        self.title_dialog("New game","Untitled game",create,templates)

    def remix(self):
        if not self.project:return
        ident=self.project["id"];draft=self.source()
        def duplicate(title,template):
            # Validate before creating so an invalid edit leaves the library untouched.
            Game(draft,seed=1)
            item=self.store.duplicate_project(ident,title)
            if item["source"]!=draft:
                item=self.store.update_project(item["id"],draft,item["revision"])
            self.poll();self.load(item);self.status_msg.set_text("Created remix")
        self.title_dialog("Remix game",self.project["title"]+" remix",duplicate)

    def import_cartridge(self):
        chooser = Gtk.FileDialog(title="Import LAB cartridge")
        allowed = Gtk.FileFilter()
        allowed.set_name("LAB cartridge (*.lab)")
        allowed.add_suffix("lab")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(allowed)
        chooser.set_filters(filters)

        def chosen(dialog, result):
            try:
                selected = dialog.open_finish(result)
                path = selected.get_path()
                if not path:
                    raise StoreError("Choose a cartridge from a local folder.")
                self.store.import_project(path)
                self.poll()
                self.tabs["play"].set_active(True)
                self.status_msg.set_text("Imported cartridge")
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.message(str(exc), True)
            except (StoreError, GameError, OSError) as exc:
                self.message(str(exc), True)

        chooser.open(self, None, chosen)

    def export(self):
        if not self.project:return
        if self.dirty:
            self.message("Save your source before exporting this cartridge.",True)
            self.tabs["source"].set_active(True);return
        try:
            path=self.store.export_project(self.project["id"])
            self.message(f"Exported {path}")
        except (StoreError,OSError) as exc:self.message(str(exc),True)

    def bridge(self):
        dialog=Gtk.Window(transient_for=self,modal=True,title="MCP connection")
        dialog.set_default_size(425,-1)
        panel=pad(box(True,12,"dialog-content"),20);dialog.set_child(panel)
        panel.append(label("MCP connection","dialog-title"))
        panel.append(label("An MCP client can create, edit, playtest and export games in this library. Opening a game from a client selects it here.", "description", True))
        panel.append(label("Try in your connected client","overline"))
        prompt="Use LAB to make a simple falling-block game for my Pocket Computer. Open it in Studio and playtest a hard drop."
        body=label(prompt,None,True);body.set_selectable(True);panel.append(body)
        actions=box(spacing=6);actions.set_halign(Gtk.Align.END);panel.append(actions)
        def copy():
            self.get_clipboard().set(prompt)
            self.message("Copied MCP prompt.");dialog.close()
        actions.append(button("Copy prompt",copy));actions.append(button("Done",dialog.close,"primary-action"))
        dialog.present()

    def on_close(self,*_):
        if not self.skip_close_confirm and (self.dirty or self.drafts):
            def discard():
                self.skip_close_confirm=True;self.close()
            self.confirm("Close with unsaved drafts?","Your saved cartridges stay in the local library.","Discard drafts",discard)
            return True
        Gtk.StyleContext.remove_provider_for_display(self.get_display(),self.led_style)
        for name in ("poll_timer","frame_timer","highlight_timer"):
            timer=getattr(self,name,0)
            if timer:GLib.source_remove(timer);setattr(self,name,0)
        return False


class StudioApp(Gtk.Application):
    def __init__(self):
        flags = Gio.ApplicationFlags.NON_UNIQUE if os.environ.get("LAB_STUDIO_ISOLATED") == "1" else Gio.ApplicationFlags.DEFAULT_FLAGS
        super().__init__(application_id="us.lab.PocketStudio", flags=flags)
        self.window=None

    def do_activate(self):
        if self.window is None:
            provider=Gtk.CssProvider()
            provider.load_from_path(str(Path(__file__).with_name("studio.css")))
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.window=StudioWindow(self)
        self.window.present()


def run():
    return StudioApp().run([sys.argv[0]])


if __name__=="__main__":
    raise SystemExit(run())
