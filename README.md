<div align="center">
    <a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Tangerine&weight=700&size=37&duration=3000&pause=1000&color=8C2BFF&center=true&vCenter=true&width=200&lines=PartySense" alt="PartySense" /></a>
</div>

<div align="center">
  <img src="./party_app/static/img/logo.png" alt="Project Logo" width="400" />
</div> 

## 📝 Overview

**PartySense** is a music application that integrates personalized music playback with IoT features to enhance party experiences. Currently, the speaker functionality is implemented, while light and motion detection are under development.

### Key Features
- 🎵 **Save Favorite Music:** Keep track of songs you love in your personalized library.
- 🔍 **Autocomplete Search:** Quickly find songs with smart search suggestions.
- 🔑 **Google Login:** Securely access your music and settings.
- ⏱️ **Real-Time Updates:** Enjoy minimal delay between commands and responses.

---

## 🚀 Getting Started

### Prerequisites

To set up PartySense, ensure you have:

1. **Hardware:**
   - Raspberry Pi (Zero 2W or equivalent).
   - Speaker compatible with Raspberry Pi GPIO (e.g., CQRobot Speaker).

2. **Software:**
   - Python 3.12+ environment.
   - Flask framework.
   - MongoDB database.
   - PubNub for real-time communication.

3. **Miscellaneous:**
   - Breadboards and a stable internet connection.

### Installation

**Clone the repository:**
```bash
$ git clone https://github.com/your-repo/PartySense.git
$ cd PartySense
```

**Setup the server application:**
```bash
$ cd party_app
$ pip install -r requirements.txt
$ touch .env
```
Update the `.env` file with the following keys:
```env
SECRET_FLASK_KEY=
MONGODB_URI=

PUBNUB_PUBLISH_KEY=
PUBNUB_SUBSCRIBE_KEY=
PUBNUB_SECRET_KEY=
PUBNUB_USER_ID=

YOUTUBE_API_KEY=

```

**Setup the Raspberry Pi application:**
```bash
$ cd party_pi
$ pip install -r requirements.txt
$ touch .env
```
Update the `.env` file with similar keys as above.

**Run the applications:**
- For `party_app` (server):
```bash
$ python app.py
```
- For `party_pi` (Raspberry Pi):
```bash
$ python main.py
```

---

### Workflow
1. **User Login:** Users log in via Google to access their playlists and settings.
2. **Music Playback:** User playlists are retrieved from MongoDB, or defaults are used.
3. **Real-Time Updates:** PubNub handles communication between user devices and the system.
4. **Data Storage:** MongoDB stores user preferences and playlists securely.

---

## 📊 Features and Benefits

| Feature                         | Description                                      | Benefit                                |
|---------------------------------|--------------------------------------------------|----------------------------------------|
| 🎶 Save Favorite Music          | Easily mark and save your favorite songs.        | Quick access to your top tracks.       |
| 🔍 Autocomplete Search          | Get suggestions as you type.                     | Faster and smarter searches.           |
| 🔐 Google Login                 | Secure user authentication.                      | Simplifies login and access.           |
| ⏱️ Real-Time Feedback           | Quick responses to user actions.                | Smooth and interactive experience.     |

---

### Contribution Guidelines
1. Fork the repository.
2. Create a new branch for your feature: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature description"`.
4. Push to your branch: `git push origin feature-name`.
5. Submit a pull request for review.

---

## 💡 Future Enhancements
- **Hardware Integration:** Complete implementation for light and motion detection.
- **Scalability:** Optimize for handling more users simultaneously.

---
