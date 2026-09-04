# 🎵 Track Commands

Get lyrics and discover musical relationships through samples and interpolations.

---

## ✍️ Lyrics

### !lyrics (`!lr`)

Fetch and display the lyrics for the track you're currently listening to on Last.fm.

The lyrics are synced and displayed in an easy-to-read, paginated format perfect for singing along or understanding the words!

**Requirements:**

- You must have set your Last.fm username using [`!setlastfm`](users.md#setlastfm)
- You must be currently listening to a track on Last.fm (or have recently played one)

!!! example "Usage Examples"
    ```
    !lyrics
    !lr
    ```

!!! info "Data Source"
    Lyrics are fetched from various sources and may not be available for all tracks.

---

## 🎶 Samples & Covers

### !samples (`!s`)

Check samples, interpolations, and songs that sample a specific track.

The command displays relationships between the track and other songs, including:
- **Samples** – Songs that directly sample this track
- **Interpolations** – Songs that reinterpret or re-record parts of this track
- **Sampled In** – Songs that this track samples from

**Options:**

- **Name** (optional) – The name of the track you want to search for. Defaults to your currently playing track on Last.fm.

!!! example "Usage Examples"
    ```
    !samples
    !s The Beatles - Come Together
    ```

### !covers (`!c`)

Check if a track is a cover or has covers.

Displays two sections if available:
- **Cover of** – This track is a cover of another artist's original
- **Covers** – Other artists who have covered this track

**Options:**

- **Name** (optional) – The name of the track you want to search for. Defaults to your currently playing track on Last.fm.

!!! example "Usage Examples"
    ```
    !covers
    !c Joy Division - Love Will Tear Us Apart
    ```

!!! info "Data Source"
    Cover relationships are fetched from Genius and may not be available for all tracks.
