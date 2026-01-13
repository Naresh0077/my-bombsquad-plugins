# ba_meta require api 9
import babase
import ba
import _ba

# Plugin Manager metadata (REQUIRED)
plugman = dict(
    plugin_name="Character Chooser",
    description="Choose characters from lobby (API 9 compatible)",
    authors=[
        {"name": "YourName"}
    ],
    version="1.0.0",
)

# ba_meta export babase.Plugin
class Main(babase.Plugin):

    def on_app_running(self):
        # This confirms the plugin is loaded
        babase.screenmessage("Character Chooser loaded!", color=(0, 1, 0))

        # Import lobby only when app is running (safe for API 9)
        from ba import _lobby
        from ba._lobby import ChangeMessage, PlayerReadyMessage
        from ba._enums import InputType
        from ba._language import Lstr
        from ba._gameutils import animate, animate_array
        from ba._profile import get_player_profile_colors
        import weakref

        # -------- PATCHED CHOOSER INIT -------- #
        def chooser_init(self, vpos, sessionplayer, lobby):
            self._vpos = vpos
            self._lobby = weakref.ref(lobby)
            self._sessionplayer = sessionplayer
            self._dead = False
            self._ready = False
            self.characterchooser = False

            self._click_sound = _ba.getsound('click01')
            self._deek_sound = _ba.getsound('deek')
            self._mask_texture = _ba.gettexture('characterIconMask')

            self.bakwas_chars = [
                "Lee", "Todd McBurton", "Zola", "Butch", "Witch", "warrior",
                "Middle-Man", "Alien", "OldLady", "Gladiator", "Wrestler",
                "Gretel", "Robot"
            ]

            self.reload_profiles()

            self._character_names = [
                n for n in _ba.app.spaz_appearances
                if n not in self.bakwas_chars
            ]

            self._selected_team_index = lobby.next_add_team

            self._random_color, self._random_highlight = (
                get_player_profile_colors(None)
            )

            offset = _ba.app.lobby_random_char_index_offset
            self._character_index = (
                (sessionplayer.inputdevice.id + offset)
                % len(self._character_names)
            )

            self._profileindex = self._select_initial_profile()
            self._profilename = self._profilenames[self._profileindex]

            self._text_node = _ba.newnode(
                'text',
                delegate=self,
                attrs={
                    'position': (-100, self._vpos),
                    'maxwidth': 190,
                    'shadow': 0.5,
                    'h_align': 'left',
                    'v_align': 'center',
                    'v_attach': 'top'
                }
            )

            self.icon = _ba.newnode(
                'image',
                owner=self._text_node,
                attrs={
                    'position': (-130, self._vpos + 20),
                    'mask_texture': self._mask_texture,
                    'attach': 'topCenter'
                }
            )

            animate(self._text_node, 'scale', {0: 0, 0.1: 1})
            animate_array(self.icon, 'scale', 2, {0: (0, 0), 0.1: (45, 45)})

            self.update_from_profile()
            self._update_text()

        # -------- READY HANDLER -------- #
        def chooser_set_ready(self, ready):
            from ba._general import Call

            if not ready:
                self.characterchooser = False
                self._ready = False

                self._sessionplayer.assigninput(
                    InputType.UP_PRESS,
                    Call(self.handlemessage, ChangeMessage('profileindex', -1))
                )
                self._sessionplayer.assigninput(
                    InputType.DOWN_PRESS,
                    Call(self.handlemessage, ChangeMessage('profileindex', 1))
                )
                self._sessionplayer.assigninput(
                    InputType.PUNCH_PRESS,
                    Call(self.handlemessage, ChangeMessage('ready', 1))
                )

                self._update_text()
                return

            self.characterchooser = True
            self._ready = True

            self._sessionplayer.assigninput(
                InputType.UP_PRESS,
                Call(self.handlemessage, ChangeMessage('characterchooser', -1))
            )
            self._sessionplayer.assigninput(
                InputType.DOWN_PRESS,
                Call(self.handlemessage, ChangeMessage('characterchooser', 1))
            )
            self._sessionplayer.assigninput(
                InputType.BOMB_PRESS,
                Call(self.handlemessage, ChangeMessage('ready', 0))
            )

            self._update_text()
            _ba.getsession().handlemessage(PlayerReadyMessage(self))

        # -------- MESSAGE HANDLER -------- #
        def chooser_handlemessage(self, msg):
            if not isinstance(msg, ChangeMessage) or self._dead:
                return

            if msg.what == 'characterchooser':
                _ba.playsound(self._click_sound)
                self._character_index = (
                    self._character_index + msg.value
                ) % len(self._character_names)
                self._update_text()
                self._update_icon()

            elif msg.what == 'profileindex':
                _ba.playsound(self._deek_sound)
                self._profileindex = (
                    self._profileindex + msg.value
                ) % len(self._profilenames)
                self.update_from_profile()

            elif msg.what == 'ready':
                self._set_ready(msg.value == 1)

        # -------- TEXT UPDATE -------- #
        def chooser_update_text(self):
            if not self._text_node:
                return

            if self._ready and self.characterchooser:
                txt = f"{self._getname()}\n{self._character_names[self._character_index]}"
                self._text_node.scale = 0.8
            else:
                txt = self._getname(full=True)
                self._text_node.scale = 1.0

            self._text_node.text = Lstr(value=txt)
            self._text_node.color = _ba.safecolor(self.get_color()) + (1,)

        # APPLY PATCH
        _lobby.Chooser.__init__ = chooser_init
        _lobby.Chooser._set_ready = chooser_set_ready
        _lobby.Chooser.handlemessage = chooser_handlemessage
        _lobby.Chooser._update_text = chooser_update_text
