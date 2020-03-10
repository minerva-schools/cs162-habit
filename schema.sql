.mode column
.headers ON
PRAGMA foreign_keys = ON;

CREATE TABLE Users(
	UserID INTEGER PRIMARY KEY,
	FirstName VARCHAR (20),
	LastName VARCHAR (20),
	Username VARCHAR (20),
	Password VARCHAR (20) --is there some special field type for that?
);

CREATE TABLE Habits(
	HabitID INTEGER PRIMARY KEY,
	UserID INTEGER,
	Title VARCHAR (50),
	Description VARCHAR (300),
	DateCreated DATE, -- Omitted time because it felts less relevant
	Active BOOLEAN, -- Specify if it's an active habit or not (instead of deletion)	
	FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

/* 
The Milestones table includes all individual events that are created as a result
of an active habit, e.g. a specific instance of 'Learn Spanish for 2 Hours a Week' 
I am not yet sure what functionality we want to give users, so that's a basic version.
*/
CREATE TABLE Milestones(
	MilestoneID INTEGER PRIMARY KEY,
	HabitID INTEGER,
	Time DATETIME,
	Title VARCHAR(20),
	UserSucceeded BOOLEAN, -- whether the user practiced their habit on this event
	FOREIGN KEY (HabitID) REFERENCES Habits(HabitID)
);


/* 
I am not sure about needing a table for notifications as well - that might be another one
*/ 
