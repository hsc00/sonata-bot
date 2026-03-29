# 👤 User Commands

Manage your profile, import ratings, and view community statistics.

---

## ⚙️ Setup & Configuration

### !setlastfm

Link your Last.fm account to enable automatic track detection across many commands.

This allows the bot to automatically fetch what you're currently listening to.

**Options:**

- **Username** – Your [Last.fm](https://www.last.fm/) username

!!! example "Usage Examples"
    ```
    !setlastfm myusername
    ```

### !importratings (`!i`)

Import all your ratings from a CSV file exported from RateYourMusic.

This is the core feature that enables all rating-based functionality in Sonata.

**How to get your CSV file:**

1. Go to [RateYourMusic Export](https://rateyourmusic.com/musicexport)
2. Click "Begin export..." and wait for the export to complete
3. Download your CSV file
4. Attach the file when running this command

**To attach a file:**

- Drag and drop the file into Discord, then type the command
- Or click the ➕ button → "Upload a file" → Select your CSV → Type the command

!!! example "Usage Examples"
    ```
    !importratings (with CSV file attached)
    !i (with CSV file attached)
    ```

!!! info "Import Time"
    The import process may take a while depending on the number of ratings you have. Please be patient and do not try to re-run the command while the import is still in progress.

!!! warning "Data Overwrite"
    Importing ratings will **overwrite** any existing ratings you have in the bot. This ensures your data stays in sync with RateYourMusic.

---

## 📊 Statistics & Profiles

### !profile

View detailed statistics about your (or another user's) music taste, including:

- Average rating score
- Total releases rated
- Number of unique artists rated

**Options:**

- **User** (optional) – Select another user by mention or Discord user ID. If not provided, shows your own profile.

!!! example "Usage Examples"
    ```
    !profile
    !profile @user
    ```

### !ratingsrank (`!rr`)

View a leaderboard of server members ranked by the number of ratings they have submitted.

!!! example "Usage Examples"
    ```
    !ratingsrank
    !rr
    ```
