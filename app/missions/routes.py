from flask import Blueprint, render_template, redirect, url_for, request, Response, flash
from sqlalchemy import desc, or_
from app import db
from werkzeug import secure_filename

from .models import Mission
from app.database.database import CmpMission, CmpComment

from config import SERVER_MISSION_FOLDER, TEMPORARY_MISSION_FOLDER

import datetime
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
            created = datetime.datetime.now()
            created.strftime("%Y-%m/%d %H:%M")

            # fetch the author from file
            with open(SERVER_MISSION_FOLDER+file, 'r', encoding="utf8", errors='ignore') as missionfile:
                mission_contents = missionfile.readlines()


            for line in mission_contents:
                line = line.strip()

                if "author" in line:
                    author = re.findall(r'"([^"]*)"', line)


            temp_mission = CmpMission(temp_name, world_name, author[0], file, "Accepted", "", 0, created, SERVER_MISSION_FOLDER)
            folder_missions.append(temp_mission)

            # this test needs to be first, wtf
            if temp_mission not in database_missions:
                db.session.add(temp_mission)


    db.session.commit()



def missions_in_database():
    return db.session.query(CmpMission).filter(or_(CmpMission.status == "Accepted", CmpMission.status == "Unknown"))




@mod_missions.route('/submissions/')
def display_submissions():
    missions = db.session.query(CmpMission).filter(or_(CmpMission.status != "Accepted")).all()
    missions.sort(key=lambda x: x.created, reverse=False)
    return render_template('modqueue.html', data=missions, today=datetime.date.today())



@mod_missions.route('/submissions/submit/', methods=['POST', 'GET'])
def submit_mission():
    error = None
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            min_play = request.form['min_play']

            if valid_mission(file, min_play):

                file.save(TEMPORARY_MISSION_FOLDER + file.filename)


                staff_notes = request.form['freetext']

                # remove versoning numbers
                temp_name = re.sub('(?:[.](.*)|_[vV]([0-9]+(.*))?)', '', file.filename)
                world_name = file.filename.split('.')[1]
                created = datetime.datetime.now()
                created.strftime("%Y-%m/%d %H:%M")
                temp_mission = CmpMission(temp_name, world_name, "soju", file.filename, "Evaluating", staff_notes, min_play, created, TEMPORARY_MISSION_FOLDER)

                # Send it to the db
                db.session.add(temp_mission)
                db.session.commit()
                obj = db.session.query(CmpMission).order_by('-id').first()
                flash("Your mission has been sucsessfully been submitted.")
                # Email routine should kick in here
                return redirect(url_for('missions.view_submission', id=obj.id))

        else:
            flash("Please only submit pbo files.")




    return render_template('submit.html', error=error)


@mod_missions.route('/submissions/view/<id>', methods=['POST', 'GET'])
def view_submission(id):
    selected_mission=db.session.query(CmpMission).filter(CmpMission.id == id and CmpMission.status != "Accepted").first()
    if selected_mission is not None and selected_mission.status != "Accepted":

        mission_comments = db.session.query(CmpComment).filter(CmpComment.mission_id == id).all()

        if request.method == 'POST':
            if 'Comment' in request.form.values():
                commenText = request.form['comment']
                created = datetime.datetime.now()
                created.strftime("%Y-%m/%d %H:%M")
                temp_obj = CmpComment(id, commenText, created, "soju")
                db.session.add(temp_obj)
                db.session.commit()
                flash("Your comment has been submitted")



            else:
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
        mission_comments.sort(key=lambda x: x.created, reverse=True)
        return render_template('view.html', mission = selected_mission, statuses=status, comments=mission_comments, folder=TEMPORARY_MISSION_FOLDER)

    return redirect(url_for('missions.display_submissions'))

def allowed_file(filename):
    # Must log attempts at malicious files and notify staff
    ALLOWED_EXTENSIONS = set(['pbo'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def valid_mission(file, min_play):
    #check file name
    mission_name_split = file.filename.split("_")

    if len(mission_name_split) >= 2:

        provided_playable = mission_name_split[1]
        try:
            provided_playable = int(re.sub('[^0-9]','', provided_playable))
        except ValueError:
            flash("Your mission name appears to not follow the naming convention.")
            return False

        raw_text = file.read()
        file.seek(0)
        mission_contents = str(raw_text)


        actual_playable = []
        actual_playable.append(int(mission_contents.count("isPlayable=1;")))
        actual_playable.append(int(mission_contents.count('player="PLAYER COMMANDER";')))

        if not (provided_playable in actual_playable):
            flash("Your mission has " + str(actual_playable[0]) + " " + str(actual_playable[1]) + " While file name is " + str(provided_playable))
            return False

        if not re.search('ark+_[a-z]+[0-9]+_.+[.].+[.]pbo', file.filename):
            flash("Your mission name appears to not follow the naming convention.")
            return False

        if int(min_play) > provided_playable:
            flash("Minimum amounts of players are higher than actual playable units")
            return False


        return True
    else:
        return False
