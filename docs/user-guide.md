# User guide

**English** · [Русский](user-guide.ru.md)

The app runs in a browser (http://localhost:8000 in the Docker setup). Accounts are created by an administrator; there is no self-registration. The interface is in Russian; button and section names below are given in English with the Russian label in parentheses where it helps.

## 1. Signing in and roles

1. Open the app and enter the email and password issued by your administrator.
2. After five failed attempts in a row, sign-in is locked for 15 minutes.
3. Sign out from the user menu in the top right corner.

| Role | What you can do |
|---|---|
| Employee | browse rooms and the calendar, search for free rooms, create, change and cancel **your own** bookings, receive notifications |
| Administrator | everything above, plus managing rooms, equipment and users, and statistics |

"Administration" and "Statistics" are opened from the user menu (administrators only).

## 2. Booking rules

- Working hours are **08:00–20:00**; a booking must fit within a single day.
- Start and end are multiples of **15 minutes**; duration is from 15 minutes to 8 hours.
- You cannot book in the past.
- Attendees: from 1 up to the room capacity.
- Back-to-back bookings (10:00–11:00 and 11:00–12:00) do not conflict.
- A room cannot have two overlapping bookings. If a slot is taken, the app shows who holds it and when.
- A booking that has started can only be shortened (earlier end) or cancelled; a finished booking cannot be changed or cancelled.
- An inactive room cannot be booked.

## 3. Calendar and booking

The home page is a "rooms × time" calendar for the selected day.

1. Use the arrows and "Today" to switch days. The "from N people" filter keeps rooms with enough capacity.
2. Pick a room with the chips above the grid.
3. Click free time in the grid, or drag to select the interval. Alternatively use the "+" ("New booking") button.
4. In the form, check date, start, end and room, enter a title and the number of attendees, and press "Book" ("Забронировать").

Calendar colours distinguish your bookings, other people's bookings and past time. A line marks the current moment.

**If the time is taken**, the form shows "This time is already taken" with the title, time and organiser of the conflicting booking. The "Show in calendar" link jumps to that day; or pick another time.

## 4. Rooms

The "Rooms" section shows cards with capacity, equipment and current status ("Busy until…" / "Free until…").

- Filter by minimum capacity and equipment (chips can be combined).
- "Schedule" opens the room page: a weekly grid, navigation by week and by date. On a phone one day is shown, and days are switched with the strip above the grid.
- You can also book from here: select time in the grid or press "Book".

## 5. Searching for a free room

"Search" section: enter the date, "From" and "To" times, the number of attendees and, if needed, the required equipment, then press "Find".

- Results list free rooms with a day timeline: your interval, busy periods and the current moment.
- "Book" next to a room opens the booking form with the time pre-filled.
- If nothing fits, change the time, reduce the number of attendees or drop equipment requirements.

## 6. My bookings

"My bookings" has three tabs: "Upcoming", "Past", "Cancelled". Bookings are grouped by day.

- **Edit** changes time, room, title or attendees; overlap checks run again.
- **Cancel** (trash button) asks for confirmation in a dialog, then moves the booking to "Cancelled" and frees the slot. Cancelled bookings stay in history and reports.
- A booking starting within the next hour shows "in N min".

## 7. Notifications

The bell in the header shows the unread count (refreshed every 30 seconds).

| Notification | When it arrives |
|---|---|
| "Starting soon" | 15 minutes before your booking starts |
| "Booking changed" | another user (an administrator) changed your booking |
| "Booking cancelled" | another user (an administrator) cancelled your booking |

Clicking a notification marks it read; "Mark all read" marks everything. Your own actions do not create notifications.

## 8. Administration (administrators only)

User menu → "Administration". Three tabs:

**Rooms.** "Add room": name, location, capacity, equipment. The pencil edits a room. Rooms are never deleted: an inactive room is hidden from the calendar and search, while its booking history is kept.

**Equipment.** Add, rename and delete (with a confirmation dialog). Equipment assigned to rooms cannot be deleted; remove it from the rooms first (the app shows an error message).

**Users.**
- Create: full name, email, role. A **temporary password is shown once** after creation: copy it and pass it to the user.
- Shield — change role (employee / administrator); key — reset password (after confirmation; the new temporary password is shown once); lock icon — block or unblock.
- A blocked user cannot sign in; their future bookings stay.
- You cannot block or demote yourself (the row says "this is you").

## 9. Statistics (administrators only)

User menu → "Statistics". Choose the period with presets or the "From" / "To" fields.

- **Summary:** number of bookings, cancelled ones and their share, average duration, total booked hours.
- **Room utilisation:** share of working time booked, per room.
- **Peak hours:** a "weekday × hour" heat map.
- **Users:** bookings and cancellations per employee.

Each block can be exported with its "CSV" button.

## 10. FAQ

- **I cannot book: "time is taken".** Pick another time or room; "Show in calendar" leads to the conflicting booking.
- **A room is missing.** It is inactive, or filtered out by capacity or equipment.
- **I cannot edit a booking.** It has already finished, or you are trying to extend one that has started (only shortening is allowed), or it is not yours.
- **Forgot my password.** Ask an administrator to reset it and issue a temporary one.
- **A booking outside working hours is rejected.** Only 08:00–20:00 in the organisation's time zone is allowed.
