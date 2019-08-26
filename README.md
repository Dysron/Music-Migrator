# Music Migrator
Takes local files on a device and adds them to your selected playlist on your favorite music streaming application.

**Getting Started**
______
**Installing**
1. Download the repository
2. Change the working directory to the downloaded repository
3. Initiate a virtual environment (or don't...up to you)
4. pip install mutagen, spotipy (necessary for song metadata and accessing Spotify)

**Before Using**
- Create an app through https://developer.spotify.com
- Create a config file in the repo called `config.ini`
- In the config file add these lines, replacing the brackets and the text in the brackets with the correct values:
  ```
  [DEFAULT]
  client_id= [INSERT YOUR APP's CLIENT ID HERE]
  client_secret= [INSERT YOUR APP's CLIENT SECRET HERE]
  ```


**How to Use**
- Run migratory.py and the login screen will load.
![Login Screen](https://user-images.githubusercontent.com/22123705/28049864-1dc7559a-65c8-11e7-9fba-8fe21a1f94b4.png)  
- Enter your username and a link will open in the browser to log in with Spotify.
- Log in and copy and paste the url you are redirected to into the terminal.
- Press "Search for Files" and upload music files
![Main Page](https://user-images.githubusercontent.com/22123705/28741778-18b25b90-73ec-11e7-8d3f-4b2c9e4375a1.png)
- Press "Add to Playlist" or "Add to Your Music" and watch either your selected playlist or the Songs playlist (depending on your button choice) update with the newly added tracks

**Built With**
______
[Spotipy](https://github.com/plamere/spotipy)  - used to add tracks to playlists  
[Mutagen](https://github.com/quodlibet/mutagen) - used to retrieve music metadata for searching

**Author**
______
- Dysron Marshall
