from tkinter import *
from tkinter import messagebox, filedialog, ttk
import spotipy
import spotipy.util as util
import mutagen
from mutagen import id3
import re
import configparser


class Login(Frame):
    def __init__(self, root):
        self.root = root
        self.root.title("Welcome")
        super().__init__(self.root)

        # create the labels and boxes for the usernames and passwords
        self.username_text = Label(self, text="Username:")
        self.username_entered = Entry(self)

        # put the labels and boxes in the proper positions
        self.username_text.grid(row=0, column=0)
        self.username_entered.grid(row=0, column=1)

        self.login_button = Button(self, text="Login", command=self.log_user_in)
        self.login_button.grid(row=1)
        self.pack()

    def log_user_in(self):

        username = self.username_entered.get()
        scopes = "playlist-read-private	playlist-modify-public playlist-modify-private user-library-read " \
                 "user-library-modify "
        try:
            config = configparser.ConfigParser()
            config.read("config.ini")
            token = util.prompt_for_user_token(username=username, scope=scopes,
                                               client_id=config["DEFAULT"]["client_id"],
                                               client_secret=config["DEFAULT"]["client_secret"],
                                               redirect_uri="http://127.0.0.1:8000/")
            self.client = spotipy.Spotify(auth=token)
        except:
            messagebox.askretrycancel(title="Incorrect Login", message="Incorrect Login")
            raise
        self.logged_in(self.client, username)

    def logged_in(self, spotify_client, username):
        app_page = MainPage(Tk(), spotify_client, username)
        self.root.destroy()
        app_page.mainloop()


class MainPage(Frame):
    def __init__(self, root, spotify_client, username):
        root.title("Spotify Migrator")
        super().__init__(root)
        self.spotify_client = spotify_client
        self.username = username

        self.user_playlists = Playlists(self, spotify_client, self.username)
        self.selected_files = LoadedFiles(self)

        # inner frame 1
        self.button_frame = Frame(self)
        self.search_button = Button(self.button_frame, text="Search for Files", command=self.ask_for_filenames)
        self.migrate_button = Button(self.button_frame, text="Migrate",
                                     command=lambda:
                                     self.migrate_files(self.user_playlists.playlists,
                                                        self.user_playlists.get_selected_id()))
        self.search_button.grid(row=0)
        self.migrate_button.grid(row=1)

        # inner frame 2
        self.option_frame = Frame(self)
        self.market_entry = Entry(self.option_frame)
        self.market_entry.insert(0, "Enter market (Ex. UK)")
        self.market_entry.bind("<FocusIn>", self.temporary_text_in)
        self.market_entry.bind("<FocusOut>", self.temporary_text_out)
        self.explicit_var = BooleanVar()
        self.explicit_label = Label(self.option_frame, text="Explicit")
        self.explicit_checkbox = Checkbutton(self.option_frame, variable=self.explicit_var,
                                             onvalue=True, offvalue=False, command=self.explicit_value_change)
        self.market_entry.grid(row=0)
        self.explicit_label.grid(row=1, sticky=W)
        self.explicit_checkbox.grid(row=1, sticky=E)

        # show what files could not be found (maybe not on Spotify or bad metadata)
        # self.unsuccessful_adds = Listbox(self)

        # position widgets
        self.button_frame.grid(row=0, column=0)
        self.option_frame.grid(row=0, column=1)
        self.user_playlists.grid(row=1, column=0, sticky=W)
        self.selected_files.grid(row=2, column=0, sticky=W)
        self.pack()

    def temporary_text_in(self, event):
        widget = event.widget
        default_text = "Enter market (Ex. UK)"
        if widget.get() == default_text:
            widget.delete(0, len(widget.get()))

    def temporary_text_out(self, event):
        widget = event.widget
        default_text = "Enter market (Ex. UK)"
        if widget.get() == "":
            widget.insert(0, default_text)

    def explicit_value_change(self):
        if self.explicit_var.get():
            self.explicit_var.set(False)
            return
        self.explicit_var.set(True)

    def username_blur_text(self, entry_box):
        if entry_box == "":
            entry_box["textvariable"].set("Country code: ex. US")

    # collect the files and add them to the selected_files list
    def ask_for_filenames(self):

        Tk().withdraw()
        self.files = filedialog.askopenfilenames(initialdir="/", title="Select file")

        for count, file in enumerate(self.files, start=1):
            try:
                if file.endswith(".m4a"):
                    song = mutagen.File(file)
                    name = song["\xa9nam"]
                    artist = song["\xa9ART"]
                    album = song["\xa9alb"]

                else:  # then it must be an .mp3 file - if not, then exception
                    song = id3.ID3(file)
                    name = song["TIT2"].text[0]
                    artist = song['TPE1'].text[0]
                    album = song["TALB"].text[0]
            except:
                messagebox.askretrycancel(title="Wrong File Type", message="Only select .mp3, .mp4 files")
                raise

            location = file
            details = [name, artist, album]
            for c, detail in enumerate(details):
                if isinstance(details[c], list):
                    details[c] = details[c][0]
            details.append(location)
            details = tuple(details)
            self.selected_files.load_tree(str(count), details)

    def track_regex(self, string):
        return [x.lower() for x in re.findall("[\w][^ ()]*", string)]

    def find_right_track(self, local_name_groups, list_of_tracks):
        index = 0
        most_matches = 0
        for i, track in enumerate(list_of_tracks):
            track_matches = sum([1 for x in self.track_regex(track["name"]) if x in local_name_groups])
            if track_matches > most_matches:
                most_matches = track_matches
                index = i
            if track_matches == len(local_name_groups):
                break
        return list_of_tracks[index]

    def get_track_id(self, song_from_file, explicit_preference, market):
        name = song_from_file[0]
        artist = song_from_file[1]

        local_name_groups = self.track_regex(name)
        results = self.spotify_client.search(q="artist:" + "\"" + artist + "\" " + local_name_groups[0], type="track")
        if len(market) == 2:
            tracks = [x for x in results["tracks"]["items"] if x["explicit"] == explicit_preference
                      and market in x["available_markets"]]
        else:
            tracks = [x for x in results["tracks"]["items"] if x["explicit"] == explicit_preference]

        if not tracks:
            return None
        else:
            found_track = self.find_right_track(local_name_groups, tracks)
        return found_track["id"]

    def migrate_files(self, playlists, playlist_selection):

        # get the song info to search for
        track_ids = []
        song_info = []

        # song name, artist, album,
        for child in self.selected_files.get_children():
            song_info.append(self.selected_files.item(child)["values"][:-1])

        # search for song on Spotify
        for song in song_info:
            try:
                result = self.get_track_id(song, self.explicit_var.get(), self.market_entry.get())
                if result == None:
                    # add to the unsuccessful adds treeview and move on
                    continue
                track_ids.append(result)
            except:
                pass

        self.spotify_client.user_playlist_add_tracks(user=self.username,
                                                     playlist_id=playlist_selection,
                                                     tracks=track_ids, position=0)

        # delete selected files from treeview and refresh playlists at the end of migration
        self.user_playlists.refresh()
        self.selected_files.delete(self.selected_files.get_children())


class LoadedFiles(ttk.Treeview):
    def __init__(self, root):
        super().__init__(root)
        self["columns"] = ("Name", "Artist", "Album", "Path")

        # edit the headings
        self.heading("#0", text="Track #")
        self.heading("Name", text="Name")
        self.heading("Artist", text="Artist")
        self.heading("Album", text="Album")
        self.heading("Path", text="Path")

        # edit the column configurations
        self.column("#0", anchor=CENTER, width=50)
        self.column("Name", anchor=W, width=150)
        self.column("Artist", anchor=W, width=100)
        self.column("Album", anchor=W, width=150)
        self.column("Path", anchor=W, width=250)
        self.pack()

    def load_tree(self, count, file_data):
        self.insert("", "end", text=count, values=file_data)


class Playlists(ttk.Treeview):
    def __init__(self, root, spotify_client, username):
        super().__init__(root, selectmode=BROWSE)
        self.bind('<<TreeviewSelect>>', self.on_select)
        self['show'] = "headings"
        self["columns"] = ("Name", "# of Tracks", "ID")
        self.client = spotify_client
        self.username = username

        # edit the headings
        self.heading("Name", text="Name")
        self.heading("# of Tracks", text="# of Tracks")
        self.heading("ID", text="ID")

        # edit the column configurations
        self.column("Name", anchor=W, width=150)
        self.column("# of Tracks", anchor=W, width=100)
        self.column("ID", anchor=W, width=225)

        self.playlists = self.load_lists()
        self.pack()

    def on_select(self, event):
        self.selected = event.widget.selection()

    def get_selected_id(self):
        return self.item(self.selected)["values"][2]

    def load_lists(self):
        self.playlists = self.client.user_playlists(self.username)

        for json_data in self.playlists["items"]:
            try:
                if json_data["owner"]["uri"] == "spotify:user:" + self.username:
                    name = json_data["name"]
                    song_count = json_data["tracks"]["total"]
                    playlist_id = json_data["id"]
                    self.insert("", "end", values=(name, song_count, playlist_id))
            except KeyError:
                pass
        return self.playlists

    def refresh(self):
        self.delete(*self.get_children())
        self.load_lists()


tk = Tk()
A = Login(tk)
A.mainloop()
