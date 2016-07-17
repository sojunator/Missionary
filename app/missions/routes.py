from flask import Blueprint, render_template, redirect, url_for, request, Response, flash
from sqlalchemy import desc, or_
from app import db
from werkzeug import secure_filename

from .models import Mission
from app.database.database import CmpMission

from config import SERVER_MISSION_FOLDER, TEMPORARY_MISSION_FOLDER

from datetime import datetime
import os
import re


mod_missions = Blueprint('missions', __name__, url_prefix='/missions',
                       template_folder='templates')

@mod_missions.route('/')
def display_missions():
    populate_database()
    return render_template('index.html', data=missions_in_database())


def populate_database():
    folder_missions = []
    database_missions = db.session.query(CmpMission).all()

    # build database from hardrive. 
    for file in os.listdir(SERVER_MISSION_FOLDER):
        if file.endswith(".pbo"):
            temp_name = re.sub('(?:[.](.*)|_[vV]([0-9]+(.*))?)', '', file)
            world_name = file.split('.')[1]
            created = datetime.now()
            created.strftime("%Y-%m/%d %H:%M")
            temp_mission = CmpMission(temp_name, world_name, "soju", file, "Unknown", "", 0, created, SERVER_MISSION_FOLDER)
            folder_missions.append(temp_mission)
            if temp_mission not in database_missions:
                db.session.add(temp_mission)
            

    db.session.commit()



def missions_in_database():
    return db.session.query(CmpMission).filter(or_(CmpMission.status == "Accepted", CmpMission.status == "Unknown"))
     



@mod_missions.route('/submissions/')
def display_submissions():
    return render_template('modqueue.html', data=db.session.query(CmpMission).filter(or_(CmpMission.status == "Evaluating ")))

@mod_missions.route('/submissions/submit/', methods=['POST', 'GET'])
def submit_mission():
    error = None
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            if valid_mission(file):

                file.save(TEMPORARY_MISSION_FOLDER + file.filename)

                min_play = request.form['min_play']
                staff_notes = request.form['freetext']

                # remove versoning numbers
                temp_name = re.sub('(?:[.](.*)|_[vV]([0-9]+(.*))?)', '', file.filename)
                world_name = file.filename.split('.')[1]
                created = datetime.now()
                created.strftime("%Y-%m/%d %H:%M")
                temp_mission = CmpMission(temp_name, world_name, "soju", file.filename, "Evaluating", staff_notes, min_play, created, TEMPORARY_MISSION_FOLDER)

                # Send it to the db
                db.session.add(temp_mission)
                db.session.commit()
                obj = db.session.query(CmpMission).order_by('-id').first()
                flash("Your mission has been sucsessfully been submitted. A member of the staff will take a look at your mission.")
                # Email routine should kick in here
                return redirect(url_for('missions.view_submission', id=obj.id))

        else:
            flash("Please only submit pbo files.")



       
    return render_template('submit.html', error=error)


@mod_missions.route('/submissions/view/<id>', methods=['POST', 'GET'])
def view_submission(id):
    selected_mission=db.session.query(CmpMission).filter(CmpMission.id == id).first()
    if selected_mission is not None:

        if request.method == 'POST':
            selected_mission.status = request.form['status']
            selected_mission.host_notes = request.form['host_notes']
            selected_mission.min_play = request.form['min_play']
            if selected_mission.status == "Accepted":

            # Since the mission was accepted, move it to the server folder
                try:
                    os.rename(TEMPORARY_MISSION_FOLDER +  selected_mission.raw_name, 
                            SERVER_MISSION_FOLDER +  selected_mission.raw_name)
                except FileNotFoundError:
                    return "Fatal error, the file is not in the temporary folder, blame Hidden and keep calm" # error must be expanded

                selected_mission.folder = SERVER_MISSION_FOLDER
                flash("Mission is now flagged as accepted, it has been moved to the server.")

            flash("Mission successfully updated")
            db.session.commit()


        status = ["Unknown", "Evaluating", "Broken/legacy", "Accepted", "Rejected"]

        # A tad ugly, but we need the item to be garantueed first in the list.
        status.remove(selected_mission.status) 
        status.insert(0, selected_mission.status)

        return render_template('view.html', mission = selected_mission, statuses=status)

    return "404, mission not found"

def allowed_file(filename):
    # Must log attempts at malicious files and notify staff
    ALLOWED_EXTENSIONS = set(['pbo'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def valid_mission(file):
    #check file name


    mission_name_split = file.filename.split("_")
    if len(mission_name_split) >= 2:

        provided_playable = mission_name_split[1]
        provided_playable = int(re.sub('[^0-9]','', provided_playable))

        raw_text = file.read()
        mission_contents = str(raw_text)

        actual_playable = mission_contents.count("isPlayable=1;")

        if (provided_playable != actual_playable):
            flash("Incorrect amount of playlabe units specified in your filename. Blame Hidden")
            return False

        if not re.search('ark+_[a-z]+[0-9]+_.+[.].+[.]pbo', file.filename):
            flash("Your mission name appears to not follow the naming convention.")
            return False



        return True
    else:
        return False