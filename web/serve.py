from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from web import app, db, login_manager
from .models import User, Habit, Log, Milestone

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '': #if username is empty
            flash('Please insert a username.')
            return redirect(url_for('signup'))

        if password == '': #if password is empty
            flash('Please insert a password.')
            return redirect(url_for('signup'))

        user = User.query.filter_by(username=username).first() # check if a user exists

        if user: # if a user is found, try again
            flash('Username already exists')
            return redirect(url_for('signup'))

        # create new user with the form data
        try:
            new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
            # add the new user to the database
            db.session.add(new_user)
            db.session.commit()
        except:
            db.session.rollback()
            flash('Something happened and signup failed. Please try again.')
            return redirect(url_for('signup'))

        return redirect(url_for('login'))

@app.route('/') #redirect home route
def home():
    return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # check if user actually exists
        if not user:
            flash('This username does not exist')
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash('Incorrect password')
            return redirect(url_for('login'))

        # if the username exists and the password was correct, go to the user's "dashboard" for today
        login_user(user, remember=remember)
        return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/dashboard/<current_date>', methods=['GET', 'POST'])
@login_required
def dashboard(current_date):
    if request.method == 'GET':
        #find all active habits for the user that were created before or on current_date
        habits = Habit.query.filter_by(user_id=current_user.id, active=True).filter(Habit.date_created <= datetime.strptime(current_date, '%Y-%m-%d')).all()

        if habits: #if they are habits
            for habit in habits:
                #check if no log exists for the current_date
                if not Log.query.filter_by(habit_id=habit.id, date=datetime.strptime(current_date, '%Y-%m-%d')).first():
                    #if no log exists, add a log
                    try:
                        gap = (datetime.strptime(current_date, '%Y-%m-%d').date() - habit.last_modified.date()).days #days since the habit was created/frequency changed
                        weekly_test =  gap > 0 and gap % 7 == 0
                        monthly_test =  gap > 0 and gap % 30 == 0 # assuming monthly habits occur every 30 days

                        if ((habit.frequency == 'daily')
                            or (habit.frequency == 'weekly' and weekly_test)
                            or (habit.frequency == 'monthly' and monthly_test)):# check if a log is needed
                            log = Log(
                                user_id=current_user.id,
                                habit_id=habit.id,
                                date=datetime.strptime(current_date, '%Y-%m-%d')
                                )
                            db.session.add(log)
                            db.session.commit()

                    except:
                        db.session.rollback()
                        flash('Ahh, something happened while loading this page. The page was refreshed.')
                        return redirect(url_for('dashboard', current_date=date.today()))

        #returns a habit, log iterable of all the logs for the current_date
        habit_log_iter = db.session.query(Habit, Log).filter(Habit.id == Log.habit_id, Log.date == datetime.strptime(current_date, '%Y-%m-%d'), Habit.active == True).all()

        #how many habits were completed, how many habits were not
        count = {
            'completed' : len(db.session.query(Log).filter(Log.date == datetime.strptime(current_date, '%Y-%m-%d'), Log.status==True).all()),
            'todo' : len(db.session.query(Log).filter(Log.date == datetime.strptime(current_date, '%Y-%m-%d'), Log.status==False).all()),
            'total' : len(db.session.query(Log).filter(Log.date == datetime.strptime(current_date, '%Y-%m-%d')).all())
        }

        return render_template('dashboard.html', user=current_user, date=current_date, habits=habit_log_iter, count=count)

    if request.method == 'POST':
        current_date = datetime.strptime(current_date, '%Y-%m-%d')
        if request.form.get('increment') == 'previous': #decrease current_date by one
            current_date = current_date - timedelta(days=1)
        elif request.form.get('increment') == 'next': #increase current_date by one
            current_date = current_date + timedelta(days=1)
        elif request.form.get('increment') == 'today': #return to today
            current_date = current_date.today()

        elif request.form.get('done'): #check off habits for current_date
            for checked_off_id in request.form.getlist('done'):
                try:
                    log = Log.query.filter_by(user_id=current_user.id, id=checked_off_id, date=current_date).first()
                    log.status = True

                    db.session.add(log)
                    db.session.commit()

                    try:
                        cur_habit_id = Log.query.filter_by(id=checked_off_id).first().habit_id
                        count_log = len(Log.query.filter_by(user_id=current_user.id, habit_id=cur_habit_id, status=True).all())

                        # check the total number of times the habit was logged ("count" milestones)
                        if count_log in [3,7,14,30,60]:
                            cur_habit_title = Habit.query.filter_by(id = cur_habit_id).first().title
                            flash(f'YAY! You checked off the habit "{cur_habit_title}" {count_log} days in total!')
                            get_milestone = Milestone.query.filter_by(user_id=current_user.id, habit_id=cur_habit_id, type='count', text=f'Complete the habit {count_log} times!').first()
                            get_milestone.status=True #check off milestone
                            db.session.commit()

                    except:
                        db.session.rollback()
                        flash("Oh no! We couldn't check your progress after your checked off this habit. Uncheck and recheck off?")
                        return redirect(url_for('dashboard', current_date=datetime.strptime(current_date, '%Y-%m-%d'))) #if fail, stay on the day where the user wanted to check off a habit

                    try:
                        # check the number of consecutive check-offs for the habit ("streak" milestones)
                        last_logs = Log.query.filter_by(user_id=current_user.id, habit_id = cur_habit_id, status=True).order_by(Log.date.desc())

                        # get the habit frequency ('daily', 'weekly', or 'monthly')
                        habit_freq = Habit.query.filter_by(user_id=current_user.id, id=cur_habit_id).first().frequency

                        # dictionary - will serve to convert habit "string" to a number of days
                        freq_to_days = {'daily': 1, 'weekly':7, 'monthly': 30}

                        # check the last n times the habit should have been checked:
                        for n in [3,7,14,30,60]:
                            count_logs = 1 #initialize at 1 since this happens when user logs in the habit
                            for i in range(1,n):  # starting from the current day
                                date_to_check = current_date - timedelta(days= i*freq_to_days[habit_freq])  # check the previous logs (depending on frequency, could be previous logs every 1, 7 or 30 days)
                                if date_to_check in [log.date for log in last_logs]: # if the habit was successfully checked i times ago
                                    count_logs += 1 # increment the number of consecutive logs

                            if count_logs == n: # if goal streak was achieved, celebrate and mark milestone as completed
                                flash(f"YOU ROCK! You completed the habit '{cur_habit_title}' {n} times in a row!")
                                get_streak_milestone = Milestone.query.filter_by(user_id=current_user.id, habit_id=cur_habit_id, type='streak', text=f'Complete the habit {n} consecutive times!').first()
                                get_streak_milestone.status=True #check off milestone
                                db.session.commit()

                    except:
                        flash("Oops! We couldn't keep track of your progress for this habit. Try again?")
                        return redirect(url_for('dashboard', current_date=datetime.strptime(current_date, '%Y-%m-%d'))) #if fail, stay on the day where the user wanted to check off a habit


                except:
                    db.session.rollback()
                    flash('Damn, something happened while marking this as done. Please try again.')
                    return redirect(url_for('dashboard', current_date=date.today()))



        elif request.form.get('undo-done'): #uncheck habits for current_date
            for checked_off_id in request.form.getlist('undo-done'):
                try:
                    log = Log.query.filter_by(user_id=current_user.id, id=checked_off_id).filter(Log.date.like(current_date)).first()
                    log.status = False
                    db.session.add(log)
                    db.session.commit()
                except:
                    db.session.rollback()
                    flash('Oy vey, something happened while unmarking this. Please try again.')
                    return redirect(url_for('dashboard', current_date=date.today()))

        return redirect(url_for('dashboard', current_date=datetime.strftime(current_date, '%Y-%m-%d')))

@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == 'GET':
        habits = Habit.query.filter_by(user_id=current_user.id, active=True)
        return render_template('add_habit.html', habits=habits, user=current_user)
    elif request.method == 'POST':

        try:
            #adds a habit
            habit = Habit(
                user_id=current_user.id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                frequency=request.form.get('frequency'),
                date_created=datetime.today(),
                active=True
            )

            db.session.add(habit)
            db.session.flush() #staging

            #adds a log with the current habit's id
            log = Log(
                user_id=current_user.id,
                habit_id=habit.id,
                date=date.today()
            )

            db.session.add(log)

            # Add a user-defined milestone if user inserted one:
            form = request.form.to_dict()
            new_milestone_counter = 0
            while ('new_milestone_text_' + str(new_milestone_counter)) in form.keys():
                if form['new_milestone_text_' + str(new_milestone_counter)]:
                    deadline = None
                    if form['new_milestone_deadline_' + str(new_milestone_counter)]:
                        deadline = datetime.strptime(form['new_milestone_deadline_' + str(new_milestone_counter)], '%Y-%m-%d')
                    if deadline and deadline.date() < datetime.now().date():  #check if the deadline is not in the past
                        flash('The deadline cannot be in the past!')
                        return redirect(url_for('add_habit'))
                    else:
                        milestone = Milestone(
                            user_id = current_user.id,
                            habit_id = habit.id,
                            text = form['new_milestone_text_' + str(new_milestone_counter)],
                            type = form['new_milestone_type_' + str(new_milestone_counter)],
                            deadline = deadline)
                        db.session.add(milestone)
                new_milestone_counter += 1

            # Automatically create a 'count' milestone when the habit is created
            # E.g. A 'count' milestone is achieved when the user completed the habit a total number of 3 times
            for n in [3,7,14,30,60]:  # milestone is achieved when habit is checked 3, 7, 14, 30 and 60 times total
                iteration_milestone = Milestone(user_id=current_user.id, habit_id=habit.id, type='count', text=f'Complete the habit {n} times!')
                db.session.add(iteration_milestone)

            # Automatically create "streak" milestones when the habit is created
            # E.g.streak milestone is achieved when the user completed the habit 3 consecutive days (or whatever frequency was specified)
            for n in [3,7,14,30,60]:  # milestone is achieved when habit is checked 3, 7, 14, 30 and 60 consecutive times total
                streak_milestone = Milestone(user_id=current_user.id, habit_id=habit.id, type='streak', text=f'Complete the habit {n} consecutive times!')
                db.session.add(streak_milestone)

            db.session.commit() # end of the transaction
        except:
            db.session.rollback()
            flash('Woops, there was an error adding your habit. Please try again.')
            return redirect(url_for('add_habit'))

        return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/habit/<habit_id>')
@login_required
def habit(habit_id):
    habits = Habit.query.filter_by(user_id=current_user.id, active=True)
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    milestones = Milestone.query.filter_by(habit_id=habit_id, user_id=current_user.id).all()
    return render_template('habit.html', habits=habits, habit=habit, milestones=milestones)

@app.route('/habit/<habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    if request.method == 'GET':
        habits = Habit.query.filter_by(user_id=current_user.id, active=True)
        milestones = Milestone.query.filter_by(habit_id=habit_id, user_id=current_user.id).all()
        return render_template('edit_habit.html', habits=habits, milestones = milestones, habit=habit)
    elif request.method == 'POST':
        form = request.form.to_dict()
        if 'archive' in form.keys(): #allows a user to set a habit to inactive, this will prevent habit logs from showing up on the dashboard
            habit.active = False
            try:
                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('Oops, there was an error archiving your habit. Please try again.')
                return redirect(url_for('habit', habit_id=habit.id))

            return redirect(url_for('habit', habit_id=habit.id))

        elif 'unarchive' in form.keys(): #allows a user to set a habit to active, this will allow habit logs to show up on dashboard
            habit.active = True
            try:
                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('We are sorry, there was an error activating your habit. Please try again.')
                return redirect(url_for('habit', habit_id=habit.id))


            return redirect(url_for('habit', habit_id=habit.id))

        elif 'delete' in form.keys(): #hard delete the current habit
            #TODO: it is probably a good idea to soft delete habits and not expose hard delete functionality to the user
            Log.query.filter_by(habit_id=habit.id).delete()
            Milestone.query.filter_by(habit_id=habit.id).delete()
            try:
                db.session.delete(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('There was an error deleting your habit. Please try again (or is it a sign?).')
                return redirect(url_for('habit', habit_id=habit.id))


            return redirect(url_for('dashboard', current_date=date.today()))

        elif 'title' in form.keys() or 'description' in form.keys() or 'frequency' in form.keys() or 'new_milestone_text_0' in form.keys():
            try:
                if 'title' in form.keys():
                    habit.title = form['title']
                if 'description' in form.keys():
                    habit.description = form['description']
                if 'frequency' in form.keys():
                    habit.frequency = form['frequency']

                habit.last_modified = datetime.today()

                milestones = Milestone.query.filter_by(habit_id=habit_id, user_id=current_user.id).all()

                for milestone in milestones:
                    if ('milestone_text_' + str(milestone.id)) in form.keys():
                        deadline = None
                        if form['milestone_deadline_' + str(milestone.id)]:
                            deadline = datetime.strptime(form['milestone_deadline_' + str(milestone.id)], '%Y-%m-%d')
                        milestone.text = form['milestone_text_' + str(milestone.id)]
                        milestone.type = form['milestone_type_' + str(milestone.id)]
                        milestone.deadline = deadline

                # Add a user-defined milestone if user inserted one:
                new_milestone_counter = 0
                while ('new_milestone_text_' + str(new_milestone_counter)) in form.keys():
                    if form['new_milestone_text_' + str(new_milestone_counter)]:
                        deadline = None
                        if 'new_milestone_deadline_' + str(new_milestone_counter) in form.keys():
                            deadline = datetime.strptime(form['new_milestone_deadline_' + str(new_milestone_counter)], '%Y-%m-%d')
                        if deadline and deadline.date() < datetime.now().date():  #check if the deadline is not in the past
                            flash('The deadline cannot be in the past!')
                            return redirect(url_for('add_habit'))
                        else:
                            milestone = Milestone(
                                user_id = current_user.id,
                                habit_id = habit.id,
                                text = form['new_milestone_text_' + str(new_milestone_counter)],
                                type = form['new_milestone_type_' + str(new_milestone_counter)],
                                deadline = deadline)
                            db.session.add(milestone)
                    new_milestone_counter += 1

                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('Nope, didn''t work. Redirecting ya')

            return redirect(url_for('habit', habit_id=habit.id))

@app.route('/archive') #page for all the habits that are currently set to inactive
@login_required
def archive():
    habits = Habit.query.filter_by(user_id=current_user.id, active=False).all()
    return render_template("archive.html", habits=habits)

@app.route('/active_habits') #page for all current active habits
@login_required
def active_habits():
    habits = Habit.query.filter_by(user_id=current_user.id, active=True).all()
    return render_template("active_habits.html", habits=habits)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.shell_context_processor # Makes all objects available on flask shell for easy testing
def make_shell_context():
    '''Allows to work with all objects directly in flask shell'''
    return {'db': db, 'User': User, 'Habit': Habit, 'Milestone': Milestone, 'Log': Log}

if __name__ == '__main__':
    app.run()
