import openai, os
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, abort
import uuid 
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Set up OpenAI API credentials
openai.api_key = 'xxxxx'
app.secret_key = 'your_secret_key'  # Needed for session management

conversations = {}

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Assuming a simple user check (update with your database logic)
users = {'admin': {'password': 'secret'}}

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Adding a column for user ID
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    summary = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ChatHistory {self.role}: {self.content}>'


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('interact_history'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user, remember=True)
            return  redirect(url_for('interact_history'))
        else:
            return abort(401)
    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')

@app.route("/interact_history")
@login_required
def interact_history():
    return render_template("index.html")

@app.route('/interact_history/<session_id>')
@login_required
def interaction(session_id):
    # You might pass the session_id to the template to use in further API calls or interactions
    return render_template('history.html', session_id=session_id)

interactions = {}

from flask_login import current_user  # Make sure to import current_user


@app.route("/api", methods=["POST"])
@login_required
def process_interaction():
    data = request.json.get("data")
    session_id = request.json.get("session_id")
    if not data:
        return jsonify({"error": "Content cannot be empty"}), 400

    # Check if the request is just to fetch history without processing new input
    if data == "system":
        messages = ChatHistory.query.filter_by(session_id=session_id).all()
        history = [{"role": message.role, "content": message.content} for message in messages]
        return jsonify({"history": history})

    is_first_message = ChatHistory.query.filter_by(session_id=session_id).count() < 3

    user_interaction = ChatHistory(session_id=session_id, user_id=current_user.id, role="user", content=data)
    db.session.add(user_interaction)

    if is_first_message:
        try:
            # Using ChatCompletion to generate a summary
            chat_summary = openai.ChatCompletion.create(
                model="gpt-4-turbo",  # Or use "gpt-4" if available and appropriate for your API plan
                messages=[{"role": "system", "content": f"Make sentence with keywords from this message so i can easily find this search in the future: {data}"}],
                max_tokens=30,  # Reduce max tokens to limit output length
                temperature=0.3  # Lower temperature to increase consistency and reduce creativity
            )
            summary_text = chat_summary.choices[0].message['content'].strip()
            summary_text = 'Description: '+ summary_text
            summary_interaction = ChatHistory(session_id=session_id, user_id=current_user.id, role="system", summary=summary_text, content=summary_text)
            db.session.add(summary_interaction)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to generate summary: {str(e)}"})
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": hist.role, "content": hist.content} for hist in ChatHistory.query.filter_by(session_id=session_id).all()]
        )
        processed_text = completion.choices[0].message['content']

        assistant_interaction = ChatHistory(session_id=session_id, user_id=current_user.id, role="assistant", content=processed_text)
        db.session.add(assistant_interaction)
        db.session.commit()

        return jsonify({"data": processed_text, "history": [{"role": x.role, "content": x.content} for x in ChatHistory.query.filter_by(session_id=session_id).all()]})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "data": "Failed to process data!"})

from sqlalchemy import distinct


@app.route("/api/sessions", methods=["GET"])
@login_required
def get_sessions():
    # Query to fetch sessions with at least one non-null summary.
    # It groups the results by session_id and filters out any sessions without a summary.
    sessions = db.session.query(
        ChatHistory.session_id,
        db.func.max(ChatHistory.summary).label('summary')  # Using max to get a non-null summary if available
    ).group_by(ChatHistory.session_id).having(db.func.max(ChatHistory.summary) != None).all()

    session_data = [
        {"session_id": session.session_id, "summary": session.summary}
        for session in sessions if session.summary is not None  # Additional safety check
    ]
    return jsonify(session_data)

@app.route("/api/new-session", methods=["POST"])
@login_required
def create_new_session():
    new_session_id = str(uuid.uuid4())
    # Optionally, initialize the session in the database with an empty message or set-up parameters
    new_session = ChatHistory(session_id=new_session_id, user_id=current_user.id, role='system', content='Session started')
    db.session.add(new_session)
    db.session.commit()
    return jsonify({'session_id': new_session_id})

def setup_database():
    database_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if not os.path.exists(database_path):  # Check if database file does not exist
        with app.app_context():
            db.create_all()
            print("Database created because it wasn't there.")
    else:
        print("Database already exists.")



if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
