from donut import email_utils
from donut.modules.arcfeedback import email_templates 
import flask
import pymysql.cursors


def send_confirmation_email(email, complaint_id):
    """
    Sends a confirmation email to [address] which should be an
    email address of a user as a string
    """
    msg = email_templates.received_feedback.format(get_link(complaint_id))
    subject = "Received ARC Feedback"
    email_utils.send_email(email, msg, subject)
    return


def register_complaint(data):
    """
    Inputs a complaint into the database and returns the complaint id
    associated with this complaint
    data should be a dict with keys 'course', 'msg' and optionally 'name', 'email'
    """
    # register complaint
    query = """
    INSERT INTO arc_complaint_info (course, status, uuid)
    VALUES (%s, %s, UUID())
    """
    status = 'new_msg'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, (data['course'], status))
    # grab the complaint id that we just inserted
    query = 'SELECT LAST_INSERT_ID()'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query)
        res = cursor.fetchone()
        complaint_id = res['LAST_INSERT_ID()']
    # add message to database
    add_msg(complaint_id, data['msg'], data['name'])
    # add email to db if applicable
    if data['email'] != "" :
        add_email(complaint_id, data['email'])
    return complaint_id


def add_email(complaint_id, email):
    """
    Adds an email to list of addresses subscribed to this complaint
    """
    query = """
    INSERT INTO arc_complaint_emails (complaint_id, email)
    VALUES (%s, %s)
    """
    with flask.g.pymysql_db.cursor() as cursor: 
        cursor.execute(query, (complaint_id, email))
    


def add_msg(complaint_id, message, poster):
    '''
    Adds a message to a complaint in the database
    and updates status of complaint to 'new_msg'
    if poster is None or an empty string, it will be replaced with 
    "(anonymous)"
    '''
    #add the message
    query = """
    INSERT INTO arc_complaint_messages (complaint_id, message, poster, time)
    VALUES (%s, %s, %s, NOW())
    """
    # update the status to new_msg
    query2 = """
    UPDATE arc_complaint_info SET status = 'new_msg' WHERE complaint_id = %s
    """
    if poster == "" or poster is None :
        poster = '(anonymous)'
    with flask.g.pymysql_db.cursor() as cursor: 
        cursor.execute(query, (complaint_id, message, poster))
        cursor.execute(query2, complaint_id)
    return


def get_link(complaint_id):
    """
    Gets a (fully qualified) link to the view page for this complaint id
    """
    query = 'SELECT uuid FROM arc_complaint_info WHERE complaint_id = %s'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, complaint_id)
        res = cursor.fetchone()
        if res and 'uuid' in res: 
            uuid = res['uuid']
        else:
            uuid = None
    return flask.url_for('arcfeedback.arcfeedback_view_complaint', id=uuid, _external=True) if uuid else None


def get_id(uuid):
    """
    Returns the complaint_id associated with a uuid
    or false if the uuid is not found
    """
    query = 'SELECT complaint_id FROM arc_complaint_info WHERE uuid = %s'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, str(uuid))
        if not cursor.rowcount:
            return False
        res = cursor.fetchone()
        res = res['complaint_id']
    return res


def get_messages(complaint_id):
    """
    Returns timestamps, posters, messages, and message_id's on this complaint
    in ascending order of timestamp
    """
    query ="""
    SELECT time, poster, message, message_id FROM arc_complaint_messages WHERE complaint_id = %s ORDER BY time 
    """
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, complaint_id)
        res = cursor.fetchall()
    return res
   
     
def get_summary(complaint_id):
    """
    Returns a dict with the following fields: course, status 

    """
    fields = ['course', 'status']
    query = 'SELECT ' + ', '.join(fields) + ' FROM arc_complaint_info WHERE complaint_id = %s'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, complaint_id)
        res = cursor.fetchone()
    return res

def get_course(complaint_id):
    return get_summary(complaint_id)['course']


def get_status(complaint_id):
    return get_summary(complaint_id)['status']


def get_emails(complaint_id):
    """
    Returns a list of subscribed emails for this complaint
    """
    query = 'SELECT email FROM arc_complaint_emails WHERE complaint_id = %s'
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, complaint_id)
        res = cursor.fetchall()
    emails = []
    for row in res:
        emails.append(row['email'])
    return emails


def get_all_fields(complaint_id):
    '''
    Returns a dict with emails, messages, course, status
    '''
    data = {}
    data['emails'] = get_emails(complaint_id)
    data['messages'] = get_messages(complaint_id)
    data['course'] = get_course(complaint_id)
    data['status'] = get_status(complaint_id)
    return data


def get_new_posts():
    '''
    Returns all posts with status 'new_msg' and their associated list
    of messages. Will be an array of dicts with keys complaint_id, course, 
    status, uuid, message, poster, time
    Note that message and poster refer to the latest comment on this complaint
    '''
    query = """SELECT post.complaint_id AS complaint_id, post.course AS course, post.status AS status,
    post.uuid AS uuid, comment.message AS message, comment.poster AS poster, comment.time AS time FROM arc_complaint_info post 
    INNER JOIN arc_complaint_messages comment 
    ON comment.complaint_id = post.complaint_id
    INNER JOIN (
    SELECT complaint_id, max(time) AS time FROM arc_complaint_messages GROUP BY complaint_id
    ) maxtime 
    ON maxtime.time = comment.time AND maxtime.complaint_id = comment.complaint_id
    WHERE post.status = 'new_msg'
    """
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query)
        res = cursor.fetchall()
    return res